"""ClinicalSyncModule: receives the evaluations the phone saved offline (HU12, RF6)."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from bovi.clinical.application.internal.outboundservices.external_livestock_service import (
    ExternalLivestockService,
)
from bovi.clinical.domain.model.aggregates.evaluation import Evaluation
from bovi.clinical.domain.model.commands.clinical_commands import (
    EvaluationRecord,
    SyncEvaluationsCommand,
)
from bovi.clinical.domain.model.valueobjects.class_probabilities import (
    ClassProbabilities,
    ClassProbability,
)
from bovi.clinical.domain.model.valueobjects.clinical_code import ClinicalCode
from bovi.clinical.domain.model.valueobjects.evaluation_enums import (
    BodyZone,
    EvaluationOutcome,
    ImageOrigin,
)
from bovi.clinical.domain.repositories.evaluation_repository import EvaluationRepository
from bovi.clinical.domain.services.image_storage import JPEG, ImageStorage
from bovi.shared.domain.exceptions import ValidationError
from bovi.shared.domain.exceptions.sync_errors import check_batch_size
from bovi.shared.domain.model.valueobjects.sync_result import SyncItemResult
from bovi.shared.domain.repositories.unit_of_work import UnitOfWork

_ID_TAKEN = ("id_en_uso", "El identificador de la evaluación ya está en uso. Genere uno nuevo.")
_NO_ANIMAL = (
    "animal_no_sincronizado",
    "El animal de la evaluación aún no está en la nube. Sincronice primero los animales.",
)
_NO_IMAGE = (
    "imagen_no_encontrada",
    "La foto aún no se subió. Pida una URL de subida y vuelva a intentarlo.",
)
_BAD_IMAGE = (
    "imagen_invalida",
    "La foto subida no es un JPEG válido o excede el tamaño permitido.",
)


class EvaluationCommandService:
    def __init__(
        self,
        *,
        evaluations: EvaluationRepository,
        livestock: ExternalLivestockService,
        storage: ImageStorage,
        unit_of_work: UnitOfWork,
        max_batch: int,
        max_image_bytes: int,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._evaluations = evaluations
        self._livestock = livestock
        self._storage = storage
        self._uow = unit_of_work
        self._max_batch = max_batch
        self._max_image_bytes = max_image_bytes
        self._clock = clock

    def sync(self, command: SyncEvaluationsCommand) -> list[SyncItemResult]:
        """Saves the batch without losing nor duplicating records (RNF10).

        The phone may resend the same batch after a network cut: an evaluation
        already saved answers `duplicate` and nothing changes, because an
        evaluation is immutable. Each record is checked on its own, so one bad
        record does not block the rest.
        """
        check_batch_size(len(command.evaluations), self._max_batch, "evaluaciones")
        user_id = command.user_id
        results: dict[int, SyncItemResult] = {}
        pending: dict[int, Evaluation] = {}
        now = self._clock()

        for index, record in enumerate(command.evaluations):
            try:
                pending[index] = self._to_evaluation(user_id, record, now)
            except ValidationError as error:
                results[index] = SyncItemResult.rejected(record.id, error.code, error.message)

        # 1. Already saved (a resent batch) or repeated inside this batch.
        owners = self._evaluations.owners_of(e.id for e in pending.values())
        seen: set[UUID] = set()
        for index, evaluation in list(pending.items()):
            owner = owners.get(evaluation.id)
            if owner is not None or evaluation.id in seen:
                results[index] = (
                    SyncItemResult.rejected(evaluation.id, *_ID_TAKEN)
                    if owner not in (None, user_id)
                    else SyncItemResult.duplicate(evaluation.id)
                )
                del pending[index]
            seen.add(evaluation.id)

        # 2. The animal must be synced first, and be this farmer's.
        animal_ids = {e.animal_id for e in pending.values() if e.animal_id is not None}
        owned = self._livestock.owned_animal_ids(user_id, animal_ids) if animal_ids else set()
        for index, evaluation in list(pending.items()):
            if evaluation.animal_id is not None and evaluation.animal_id not in owned:
                results[index] = SyncItemResult.rejected(evaluation.id, *_NO_ANIMAL)
                del pending[index]

        # 3. The photo must already be in S3 (HeadObject), as a JPEG within the limit.
        stats = self._storage.stat_many([e.image_key for e in pending.values()])
        for index, evaluation in list(pending.items()):
            image = stats.get(evaluation.image_key)
            if image is None:
                results[index] = SyncItemResult.rejected(evaluation.id, *_NO_IMAGE)
                del pending[index]
            elif image.size > self._max_image_bytes or image.content_type != JPEG:
                results[index] = SyncItemResult.rejected(evaluation.id, *_BAD_IMAGE)
                del pending[index]

        # 4. INSERT ... ON CONFLICT DO NOTHING: a concurrent resend is a duplicate, never a copy.
        inserted = self._evaluations.insert_new(list(pending.values()))
        for index, evaluation in pending.items():
            results[index] = (
                SyncItemResult.accepted(evaluation.id)
                if evaluation.id in inserted
                else SyncItemResult.duplicate(evaluation.id)
            )

        self._uow.commit()
        return [results[i] for i in range(len(command.evaluations))]

    @staticmethod
    def _to_evaluation(user_id: UUID, record: EvaluationRecord, now: datetime) -> Evaluation:
        return Evaluation.record(
            id=record.id,
            user_id=user_id,
            evaluated_at=record.evaluated_at,
            image_origin=ImageOrigin.parse(record.image_origin, "image_origin"),
            probabilities=ClassProbabilities(
                tuple(ClassProbability(p.label, p.probability) for p in record.probabilities)
            ),
            predicted_class=record.predicted_class,
            confidence=record.confidence,
            outcome=EvaluationOutcome.parse(record.outcome, "outcome"),
            clinical_codes=tuple(
                ClinicalCode(c.system, c.code, c.display) for c in record.clinical_codes
            ),
            catalog_version=record.catalog_version,
            model_version=record.model_version,
            inference_ms=record.inference_ms,
            animal_id=record.animal_id,
            body_zone=(BodyZone.parse(record.body_zone, "body_zone") if record.body_zone else None),
            now=now,
        )

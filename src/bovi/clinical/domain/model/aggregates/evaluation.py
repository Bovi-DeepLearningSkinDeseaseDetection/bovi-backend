from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from bovi.clinical.domain.model.valueobjects.class_probabilities import ClassProbabilities
from bovi.clinical.domain.model.valueobjects.clinical_code import ClinicalCode
from bovi.clinical.domain.model.valueobjects.evaluation_enums import (
    BodyZone,
    EvaluationOutcome,
    ImageOrigin,
)
from bovi.clinical.domain.model.valueobjects.image_key import image_key_for
from bovi.clinical.domain.model.valueobjects.lesion_class import is_healthy
from bovi.shared.domain.exceptions import ValidationError

_CONFIDENCE_TOLERANCE = 1e-4
_MAX_CLOCK_SKEW = timedelta(days=1)


def _invalid(message: str, code: str = "evaluacion_invalida") -> ValidationError:
    return ValidationError(message, code=code)


@dataclass(frozen=True, slots=True)
class Evaluation:
    """A photo analyzed on the phone with its preliminary result (HU06, HU10).

    Immutable: the phone computes the result and the backend only keeps it.
    """

    id: UUID
    user_id: UUID
    evaluated_at: datetime
    image_origin: ImageOrigin
    probabilities: ClassProbabilities
    predicted_class: str
    confidence: float
    outcome: EvaluationOutcome
    clinical_codes: tuple[ClinicalCode, ...]
    catalog_version: str | None
    model_version: str
    inference_ms: int | None
    animal_id: UUID | None
    body_zone: BodyZone | None

    @property
    def image_key(self) -> str:
        return image_key_for(self.user_id, self.id)

    @classmethod
    def record(
        cls,
        *,
        id: UUID,
        user_id: UUID,
        evaluated_at: datetime,
        image_origin: ImageOrigin,
        probabilities: ClassProbabilities,
        predicted_class: str,
        confidence: float,
        outcome: EvaluationOutcome,
        clinical_codes: tuple[ClinicalCode, ...],
        catalog_version: str | None,
        model_version: str,
        inference_ms: int | None,
        animal_id: UUID | None,
        body_zone: BodyZone | None,
        now: datetime,
    ) -> "Evaluation":
        if evaluated_at.tzinfo is None:
            raise _invalid("La fecha de la evaluación debe incluir la zona horaria.")
        if evaluated_at > now + _MAX_CLOCK_SKEW:
            raise _invalid("La fecha de la evaluación está en el futuro.")
        if not 1 <= len(model_version.strip()) <= 50:
            raise _invalid("Falta la versión del modelo (RNF17).")
        if catalog_version is not None and not 1 <= len(catalog_version) <= 20:
            raise _invalid("La versión del catálogo clínico no es válida.")
        if inference_ms is not None and not 0 <= inference_ms <= 600_000:
            raise _invalid("El tiempo de inferencia no es válido.")

        # The phone sends what it showed; it must agree with its own probabilities.
        predicted = probabilities.of(predicted_class)
        if predicted is None or predicted < probabilities.top.probability - _CONFIDENCE_TOLERANCE:
            raise _invalid("La clase predicha no es la de mayor probabilidad.")
        if abs(confidence - predicted) > _CONFIDENCE_TOLERANCE:
            raise _invalid("La confianza no coincide con la probabilidad de la clase predicha.")
        if outcome is EvaluationOutcome.HEALTHY and not is_healthy(predicted_class):
            raise _invalid("Un resultado saludable debe tener piel sana como clase predicha.")
        if outcome is EvaluationOutcome.LESION and is_healthy(predicted_class):
            raise _invalid("Un resultado con lesión no puede tener piel sana como clase predicha.")
        # Healthy skin and inconclusive results carry no code (RF4, RF11).
        if outcome is not EvaluationOutcome.LESION and clinical_codes:
            raise _invalid("Solo un resultado con lesión lleva códigos clínicos.")
        if len(clinical_codes) > 10:
            raise _invalid("Demasiados códigos clínicos.")

        return cls(
            id=id,
            user_id=user_id,
            evaluated_at=evaluated_at,
            image_origin=image_origin,
            probabilities=probabilities,
            predicted_class=predicted_class,
            confidence=confidence,
            outcome=outcome,
            clinical_codes=clinical_codes,
            catalog_version=catalog_version,
            model_version=model_version.strip(),
            inference_ms=inference_ms,
            animal_id=animal_id,
            body_zone=body_zone,
        )

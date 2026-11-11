from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from bovi.clinical.domain.model.aggregates.evaluation import Evaluation
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
from bovi.clinical.infrastructure.persistence.sqlalchemy.entities.evaluation_entity import (
    EvaluationEntity,
)


def _row(e: Evaluation) -> dict:
    return {
        "id": e.id,
        "usuario_id": e.user_id,
        "animal_id": e.animal_id,
        "fecha_hora": e.evaluated_at,
        "zona_corporal": e.body_zone.value if e.body_zone else None,
        "resultado": e.outcome.value,
        "clase_predicha": e.predicted_class,
        "confianza": e.confidence,
        "probabilidades": e.probabilities.to_json(),
        "codigos_clinicos": [code.to_json() for code in e.clinical_codes],
        "version_catalogo": e.catalog_version,
        "version_modelo": e.model_version,
        "tiempo_inferencia_ms": e.inference_ms,
        "origen_imagen": e.image_origin.value,
        "clave_imagen": e.image_key,
    }


class SqlAlchemyEvaluationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def owners_of(self, ids: Iterable[UUID]) -> dict[UUID, UUID]:
        ids = list(ids)
        if not ids:
            return {}
        rows = self._session.execute(
            select(EvaluationEntity.id, EvaluationEntity.usuario_id).where(
                EvaluationEntity.id.in_(ids)
            )
        )
        return {row.id: row.usuario_id for row in rows}

    def insert_new(self, evaluations: list[Evaluation]) -> set[UUID]:
        if not evaluations:
            return set()
        statement = (
            insert(EvaluationEntity)
            .values([_row(e) for e in evaluations])
            .on_conflict_do_nothing(index_elements=[EvaluationEntity.id])
            .returning(EvaluationEntity.id)
        )
        return set(self._session.scalars(statement))

    def page_for_user(
        self, user_id: UUID, before: tuple[datetime, UUID] | None, limit: int
    ) -> list[Evaluation]:
        e = EvaluationEntity
        statement = select(e).where(e.usuario_id == user_id)
        if before is not None:
            statement = statement.where(tuple_(e.fecha_hora, e.id) < tuple_(*before))
        statement = statement.order_by(e.fecha_hora.desc(), e.id.desc()).limit(limit)
        return [_to_domain(row) for row in self._session.scalars(statement)]

    def count_for_user(self, user_id: UUID) -> int:
        return self._session.scalar(
            select(func.count())
            .select_from(EvaluationEntity)
            .where(EvaluationEntity.usuario_id == user_id)
        )


def _to_domain(row: EvaluationEntity) -> Evaluation:
    # Rows were validated when they were synced: rebuild them as they are.
    return Evaluation(
        id=row.id,
        user_id=row.usuario_id,
        evaluated_at=row.fecha_hora,
        image_origin=ImageOrigin(row.origen_imagen),
        probabilities=ClassProbabilities(
            tuple(ClassProbability(p["label"], p["probability"]) for p in row.probabilidades)
        ),
        predicted_class=row.clase_predicha,
        confidence=row.confianza,
        outcome=EvaluationOutcome(row.resultado),
        clinical_codes=tuple(
            ClinicalCode(c["system"], c["code"], c["display"]) for c in row.codigos_clinicos
        ),
        catalog_version=row.version_catalogo,
        model_version=row.version_modelo,
        inference_ms=row.tiempo_inferencia_ms,
        animal_id=row.animal_id,
        body_zone=BodyZone(row.zona_corporal) if row.zona_corporal else None,
    )

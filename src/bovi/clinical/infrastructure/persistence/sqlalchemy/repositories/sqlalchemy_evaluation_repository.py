from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from bovi.clinical.domain.model.aggregates.evaluation import Evaluation
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

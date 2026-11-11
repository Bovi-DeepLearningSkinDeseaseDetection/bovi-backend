from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from bovi.livestock.domain.model.aggregates.animal import Animal
from bovi.livestock.domain.model.valueobjects.animal_sex import AnimalSex
from bovi.livestock.domain.model.valueobjects.ear_tag import EarTag
from bovi.livestock.infrastructure.persistence.sqlalchemy.entities.animal_entity import (
    AnimalEntity,
)


class SqlAlchemyAnimalRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def owners_of(self, ids: Iterable[UUID]) -> dict[UUID, UUID]:
        ids = list(ids)
        if not ids:
            return {}
        rows = self._session.execute(
            select(AnimalEntity.id, AnimalEntity.usuario_id).where(AnimalEntity.id.in_(ids))
        )
        return {row.id: row.usuario_id for row in rows}

    def ids_by_ear_tag(self, user_id: UUID, tags: Iterable[EarTag]) -> dict[str, UUID]:
        values = list({tag.value for tag in tags})
        if not values:
            return {}
        rows = self._session.execute(
            select(AnimalEntity.arete, AnimalEntity.id).where(
                AnimalEntity.usuario_id == user_id, AnimalEntity.arete.in_(values)
            )
        )
        return {row.arete: row.id for row in rows}

    def insert_new(self, animals: list[Animal]) -> set[UUID]:
        if not animals:
            return set()
        statement = (
            insert(AnimalEntity)
            .values(
                [
                    {
                        "id": a.id,
                        "usuario_id": a.user_id,
                        "arete": a.ear_tag.value,
                        "raza": a.breed,
                        "sexo": a.sex.value,
                        "creado_en": a.created_at,
                    }
                    for a in animals
                ]
            )
            # Any unique key: the id or (usuario_id, arete).
            .on_conflict_do_nothing()
            .returning(AnimalEntity.id)
        )
        return set(self._session.scalars(statement))

    def owned_ids(self, user_id: UUID, ids: Iterable[UUID]) -> set[UUID]:
        ids = list(ids)
        if not ids:
            return set()
        return set(
            self._session.scalars(
                select(AnimalEntity.id).where(
                    AnimalEntity.usuario_id == user_id, AnimalEntity.id.in_(ids)
                )
            )
        )

    def page_for_user(self, user_id: UUID, after_ear_tag: str | None, limit: int) -> list[Animal]:
        statement = select(AnimalEntity).where(AnimalEntity.usuario_id == user_id)
        if after_ear_tag is not None:
            statement = statement.where(AnimalEntity.arete > after_ear_tag)
        rows = self._session.scalars(statement.order_by(AnimalEntity.arete).limit(limit))
        return [_to_domain(row) for row in rows]

    def count_for_user(self, user_id: UUID) -> int:
        return self._session.scalar(
            select(func.count()).select_from(AnimalEntity).where(AnimalEntity.usuario_id == user_id)
        )


def _to_domain(row: AnimalEntity) -> Animal:
    # Rows were validated when they were saved: rebuild them as they are.
    return Animal(
        id=row.id,
        user_id=row.usuario_id,
        ear_tag=EarTag(row.arete),
        breed=row.raza,
        sex=AnimalSex(row.sexo),
        created_at=row.creado_en,
    )

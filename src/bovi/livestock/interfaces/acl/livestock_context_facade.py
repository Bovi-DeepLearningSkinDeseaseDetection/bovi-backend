"""What the livestock context offers to the other bounded contexts."""

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy.orm import Session

from bovi.livestock.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_animal_repository import (  # noqa: E501
    SqlAlchemyAnimalRepository,
)


class LivestockContextFacade:
    def __init__(self, session: Session) -> None:
        self._animals = SqlAlchemyAnimalRepository(session)

    def owned_animal_ids(self, user_id: UUID, animal_ids: Iterable[UUID]) -> set[UUID]:
        """The ids, among `animal_ids`, of animals already synced by this farmer."""
        return self._animals.owned_ids(user_id, animal_ids)

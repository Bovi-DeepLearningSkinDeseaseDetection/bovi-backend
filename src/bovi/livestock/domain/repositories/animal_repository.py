from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from bovi.livestock.domain.model.aggregates.animal import Animal
from bovi.livestock.domain.model.valueobjects.ear_tag import EarTag


class AnimalRepository(Protocol):
    def owners_of(self, ids: Iterable[UUID]) -> dict[UUID, UUID]:
        """Owner (user id) of each id that already exists, of any user."""
        ...

    def ids_by_ear_tag(self, user_id: UUID, tags: Iterable[EarTag]) -> dict[str, UUID]:
        """Id of the animals of the user with these ear tags, by tag value."""
        ...

    def insert_new(self, animals: list[Animal]) -> set[UUID]:
        """Inserts the animals, skipping any id or (user, ear tag) already taken.

        Returns the ids actually inserted.
        """
        ...

    def owned_ids(self, user_id: UUID, ids: Iterable[UUID]) -> set[UUID]: ...

    def page_for_user(self, user_id: UUID, after_ear_tag: str | None, limit: int) -> list[Animal]:
        """Animals of the user ordered by ear tag, after `after_ear_tag` (exclusive)."""
        ...

    def count_for_user(self, user_id: UUID) -> int: ...

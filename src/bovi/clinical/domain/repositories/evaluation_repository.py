from collections.abc import Iterable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from bovi.clinical.domain.model.aggregates.evaluation import Evaluation


class EvaluationRepository(Protocol):
    def owners_of(self, ids: Iterable[UUID]) -> dict[UUID, UUID]:
        """Owner (user id) of each id that already exists, of any user."""
        ...

    def insert_new(self, evaluations: list[Evaluation]) -> set[UUID]:
        """INSERT ... ON CONFLICT (id) DO NOTHING; returns the ids actually inserted."""
        ...

    def page_for_user(
        self, user_id: UUID, before: tuple[datetime, UUID] | None, limit: int
    ) -> list[Evaluation]:
        """Evaluations of the user, newest first, strictly before (evaluated_at, id)."""
        ...

    def count_for_user(self, user_id: UUID) -> int: ...

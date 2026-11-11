from collections.abc import Iterable
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

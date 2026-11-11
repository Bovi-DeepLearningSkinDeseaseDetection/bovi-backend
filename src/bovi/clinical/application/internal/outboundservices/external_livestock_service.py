from collections.abc import Iterable
from typing import Protocol
from uuid import UUID


class ExternalLivestockService(Protocol):
    """What clinical needs from livestock: which animals the farmer already synced."""

    def owned_animal_ids(self, user_id: UUID, animal_ids: Iterable[UUID]) -> set[UUID]: ...

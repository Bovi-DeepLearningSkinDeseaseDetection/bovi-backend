"""Adapter from the livestock facade to the port clinical expects."""

from collections.abc import Iterable
from uuid import UUID

from bovi.livestock.interfaces.acl.livestock_context_facade import LivestockContextFacade


class LivestockAcl:
    def __init__(self, facade: LivestockContextFacade) -> None:
        self._facade = facade

    def owned_animal_ids(self, user_id: UUID, animal_ids: Iterable[UUID]) -> set[UUID]:
        return self._facade.owned_animal_ids(user_id, animal_ids)

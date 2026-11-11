"""Race between two sync requests of the same farmer (RNF10), with an in-memory repository."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from bovi.livestock.application.internal.commandservices.animal_command_service import (
    AnimalCommandService,
)
from bovi.livestock.domain.model.aggregates.animal import Animal
from bovi.livestock.domain.model.commands.sync_animals_command import (
    AnimalRecord,
    SyncAnimalsCommand,
)
from bovi.shared.domain.model.valueobjects.sync_result import SyncStatus

USER = uuid4()
NOW = datetime(2026, 11, 11, tzinfo=UTC)


class _RacingRepository:
    """Before our INSERT runs, another request saves `stolen` (same id or same ear tag)."""

    def __init__(self, stolen: list[Animal]) -> None:
        self.rows: dict[UUID, Animal] = {}
        self._stolen = stolen

    def owners_of(self, ids):
        return {i: self.rows[i].user_id for i in ids if i in self.rows}

    def ids_by_ear_tag(self, user_id, tags):
        wanted = {t.value for t in tags}
        return {
            a.ear_tag.value: a.id
            for a in self.rows.values()
            if a.user_id == user_id and a.ear_tag.value in wanted
        }

    def insert_new(self, animals):
        for animal in self._stolen:
            self.rows[animal.id] = animal
        inserted = set()
        for animal in animals:
            taken_tag = any(
                r.user_id == animal.user_id and r.ear_tag == animal.ear_tag
                for r in self.rows.values()
            )
            if animal.id not in self.rows and not taken_tag:
                self.rows[animal.id] = animal
                inserted.add(animal.id)
        return inserted

    def owned_ids(self, user_id, ids):
        return {i for i in ids if i in self.rows and self.rows[i].user_id == user_id}


class _UnitOfWork:
    commits = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        pass


def _animal(id: UUID, tag: str, user: UUID = USER) -> Animal:
    return Animal.from_device(
        id=id, user_id=user, ear_tag=tag, breed="Holstein", sex="female", created_at=NOW
    )


def _record(id: UUID, tag: str) -> AnimalRecord:
    return AnimalRecord(id=id, ear_tag=tag, breed="Holstein", sex="female", created_at=NOW)


def test_a_concurrent_save_ends_as_duplicate_or_merged_never_as_a_copy() -> None:
    same_id, same_tag, other_users_id = uuid4(), uuid4(), uuid4()
    earlier_twin = uuid4()
    repository = _RacingRepository(
        stolen=[
            _animal(same_id, "A-1"),  # the same animal, saved by the other request
            _animal(earlier_twin, "B-2"),  # same ear tag, another id
            _animal(other_users_id, "Z-9", user=uuid4()),  # id taken by someone else
        ]
    )
    uow = _UnitOfWork()
    service = AnimalCommandService(animals=repository, unit_of_work=uow, max_batch=50)

    results = service.sync(
        SyncAnimalsCommand(
            USER,
            [_record(same_id, "A-1"), _record(same_tag, "B-2"), _record(other_users_id, "C-3")],
        )
    )

    assert [r.status for r in results] == [
        SyncStatus.DUPLICATE,
        SyncStatus.MERGED,
        SyncStatus.REJECTED,
    ]
    assert results[1].canonical_id == earlier_twin
    assert results[2].code == "reintentar"
    assert uow.commits == 1

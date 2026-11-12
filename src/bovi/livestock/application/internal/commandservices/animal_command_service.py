"""Sync of the animals registered on the phone (HU15 + HU12)."""

from uuid import UUID

from bovi.livestock.domain.model.aggregates.animal import Animal
from bovi.livestock.domain.model.commands.sync_animals_command import SyncAnimalsCommand
from bovi.livestock.domain.repositories.animal_repository import AnimalRepository
from bovi.shared.domain.exceptions import ValidationError
from bovi.shared.domain.exceptions.sync_errors import check_batch_size
from bovi.shared.domain.model.valueobjects.sync_result import SyncItemResult
from bovi.shared.domain.repositories.unit_of_work import UnitOfWork

_ID_TAKEN = ("id_en_uso", "El identificador del animal ya está en uso. Genere uno nuevo.")
_RETRY = ("reintentar", "No se pudo guardar el animal. Se intentará de nuevo.")


class AnimalCommandService:
    def __init__(
        self, *, animals: AnimalRepository, unit_of_work: UnitOfWork, max_batch: int
    ) -> None:
        self._animals = animals
        self._uow = unit_of_work
        self._max_batch = max_batch

    def sync(self, command: SyncAnimalsCommand) -> list[SyncItemResult]:
        """Saves the batch; the same batch can be sent again without duplicating (RNF10).

        An ear tag is unique per farmer (HU15, scenario 4): an animal that arrives with
        a new id but an ear tag already saved is merged into the saved one, and the
        app must use `canonical_id` from then on.
        """
        check_batch_size(len(command.animals), self._max_batch, "animales")
        user_id = command.user_id
        results: dict[int, SyncItemResult] = {}
        valid: dict[int, Animal] = {}

        for index, record in enumerate(command.animals):
            try:
                valid[index] = Animal.from_device(
                    id=record.id,
                    user_id=user_id,
                    ear_tag=record.ear_tag,
                    breed=record.breed,
                    sex=record.sex,
                    created_at=record.created_at,
                )
            except ValidationError as error:
                results[index] = SyncItemResult.rejected(record.id, error.code, error.message)

        owners = self._animals.owners_of(a.id for a in valid.values())
        by_tag = self._animals.ids_by_ear_tag(user_id, (a.ear_tag for a in valid.values()))
        seen_ids: set[UUID] = set()
        batch_tags: dict[str, UUID] = {}
        to_insert: dict[int, Animal] = {}

        for index, animal in valid.items():
            tag = animal.ear_tag.value
            if animal.id in owners:
                results[index] = (
                    SyncItemResult.duplicate(animal.id)
                    if owners[animal.id] == user_id
                    else SyncItemResult.rejected(animal.id, *_ID_TAKEN)
                )
            elif animal.id in seen_ids:
                results[index] = SyncItemResult.duplicate(animal.id)
            elif tag in by_tag:
                results[index] = SyncItemResult.merged(animal.id, into=by_tag[tag])
            elif tag in batch_tags:
                results[index] = SyncItemResult.merged(animal.id, into=batch_tags[tag])
            else:
                to_insert[index] = animal
                batch_tags[tag] = animal.id
            seen_ids.add(animal.id)

        inserted = self._animals.insert_new(list(to_insert.values()))
        lost = {i: a for i, a in to_insert.items() if a.id not in inserted}
        if lost:
            # Another request saved the same id or ear tag in the meantime.
            owners = self._animals.owners_of(a.id for a in lost.values())
            by_tag = self._animals.ids_by_ear_tag(user_id, (a.ear_tag for a in lost.values()))
        for index, animal in to_insert.items():
            if animal.id in inserted:
                results[index] = SyncItemResult.accepted(animal.id)
            elif owners.get(animal.id) == user_id:
                results[index] = SyncItemResult.duplicate(animal.id)
            elif animal.ear_tag.value in by_tag:
                results[index] = SyncItemResult.merged(animal.id, into=by_tag[animal.ear_tag.value])
            else:
                results[index] = SyncItemResult.rejected(animal.id, *_RETRY)

        self._uow.commit()
        return [results[i] for i in range(len(command.animals))]

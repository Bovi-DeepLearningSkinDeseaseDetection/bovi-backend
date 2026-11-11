from uuid import UUID

from bovi.livestock.domain.model.commands.sync_animals_command import (
    AnimalRecord,
    SyncAnimalsCommand,
)
from bovi.livestock.interfaces.rest.resources.animal_sync_resources import (
    AnimalSyncBatchResource,
)


def to_sync_animals_command(user_id: UUID, resource: AnimalSyncBatchResource) -> SyncAnimalsCommand:
    return SyncAnimalsCommand(
        user_id=user_id,
        animals=[
            AnimalRecord(
                id=a.id, ear_tag=a.ear_tag, breed=a.breed, sex=a.sex, created_at=a.created_at
            )
            for a in resource.animals
        ],
    )

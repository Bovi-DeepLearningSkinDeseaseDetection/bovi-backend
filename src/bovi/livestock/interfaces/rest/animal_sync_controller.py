"""POST /api/v1/sync/animals (HU12 + HU15)."""

from fastapi import APIRouter, Depends

from bovi.iam.interfaces.acl.iam_context_facade import AuthenticatedUserId
from bovi.livestock.application.internal.commandservices.animal_command_service import (
    AnimalCommandService,
)
from bovi.livestock.interfaces.rest.dependencies import get_animal_command_service
from bovi.livestock.interfaces.rest.resources.animal_sync_resources import (
    AnimalSyncBatchResource,
)
from bovi.livestock.interfaces.rest.transform.animal_sync_assemblers import (
    to_sync_animals_command,
)
from bovi.shared.interfaces.rest.resources.error_resource import ErrorResource
from bovi.shared.interfaces.rest.resources.sync_result_resource import SyncBatchResource

router = APIRouter(prefix="/sync", tags=["Livestock"])


@router.post(
    "/animals",
    response_model=SyncBatchResource,
    summary="Sincronizar animales",
    description=(
        "Guarda los animales registrados en el celular. Es idempotente: reenviar el mismo lote "
        "no duplica nada. Si llega un arete que el ganadero ya tiene con otro id, el animal se "
        "fusiona (`merged`) y la app debe usar `canonical_id` en adelante. Sincronice los "
        "animales antes que las evaluaciones que los usan."
    ),
    responses={401: {"model": ErrorResource}, 422: {"model": ErrorResource}},
)
def sync_animals(
    resource: AnimalSyncBatchResource,
    user_id: AuthenticatedUserId,
    service: AnimalCommandService = Depends(get_animal_command_service),
) -> SyncBatchResource:
    return SyncBatchResource.of(service.sync(to_sync_animals_command(user_id, resource)))

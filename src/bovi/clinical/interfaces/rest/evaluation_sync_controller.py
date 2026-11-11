"""POST /api/v1/sync/evaluations (HU12, RF6, RNF10)."""

from fastapi import APIRouter, Depends

from bovi.clinical.application.internal.commandservices.evaluation_command_service import (
    EvaluationCommandService,
)
from bovi.clinical.interfaces.rest.dependencies import get_evaluation_command_service
from bovi.clinical.interfaces.rest.resources.clinical_resources import (
    EvaluationSyncBatchResource,
)
from bovi.clinical.interfaces.rest.transform.clinical_assemblers import (
    to_sync_evaluations_command,
)
from bovi.iam.interfaces.acl.iam_context_facade import AuthenticatedUserId
from bovi.shared.interfaces.rest.resources.error_resource import ErrorResource
from bovi.shared.interfaces.rest.resources.sync_result_resource import SyncBatchResource

router = APIRouter(prefix="/sync", tags=["Clinical"])


@router.post(
    "/evaluations",
    response_model=SyncBatchResource,
    summary="Sincronizar evaluaciones",
    description=(
        "Recibe hasta 20 evaluaciones. Antes, la app sube cada foto con /media/upload-url y "
        "sincroniza los animales con /sync/animals. Es idempotente: una evaluación ya guardada "
        "responde `duplicate` y no cambia (la evaluación es inmutable). Cada registro se valida "
        "por separado; `accepted` y `duplicate` significan que ya está en la nube."
    ),
    responses={
        401: {"model": ErrorResource},
        422: {"model": ErrorResource},
        503: {"model": ErrorResource},
    },
)
def sync_evaluations(
    resource: EvaluationSyncBatchResource,
    user_id: AuthenticatedUserId,
    service: EvaluationCommandService = Depends(get_evaluation_command_service),
) -> SyncBatchResource:
    return SyncBatchResource.of(service.sync(to_sync_evaluations_command(user_id, resource)))

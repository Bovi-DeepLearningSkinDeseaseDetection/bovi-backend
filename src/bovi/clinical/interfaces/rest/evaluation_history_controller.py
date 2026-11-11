"""GET /api/v1/evaluations: history of the farmer to restore it (HU13, RF13)."""

from fastapi import APIRouter, Depends, Query

from bovi.clinical.application.internal.queryservices.evaluation_query_service import (
    EvaluationQueryService,
)
from bovi.clinical.domain.model.queries.get_evaluation_history_query import (
    GetEvaluationHistoryQuery,
)
from bovi.clinical.interfaces.rest.dependencies import get_evaluation_query_service
from bovi.clinical.interfaces.rest.resources.clinical_resources import (
    EvaluationHistoryPageResource,
)
from bovi.clinical.interfaces.rest.transform.clinical_assemblers import to_history_page_resource
from bovi.iam.interfaces.acl.iam_context_facade import AuthenticatedUserId
from bovi.shared.domain.model.valueobjects.page import DEFAULT_LIMIT
from bovi.shared.interfaces.rest.resources.error_resource import ErrorResource

router = APIRouter(tags=["Clinical"])


@router.get(
    "/evaluations",
    response_model=EvaluationHistoryPageResource,
    summary="Historial de evaluaciones del ganadero",
    description=(
        "De la más reciente a la más antigua. Cada evaluación trae `image_url`, una URL prefirmada "
        "para descargar su foto (15 minutos). Para restaurar: GET /animals y luego esta ruta "
        "siguiendo `next_cursor` hasta que sea null."
    ),
    responses={401: {"model": ErrorResource}, 422: {"model": ErrorResource}},
)
def list_evaluations(
    user_id: AuthenticatedUserId,
    limit: int = Query(DEFAULT_LIMIT, description="Entre 1 y 100"),
    cursor: str | None = Query(None, description="`next_cursor` de la página anterior"),
    service: EvaluationQueryService = Depends(get_evaluation_query_service),
) -> EvaluationHistoryPageResource:
    page = service.get_history(
        GetEvaluationHistoryQuery(user_id=user_id, limit=limit, cursor=cursor)
    )
    return to_history_page_resource(page)

"""GET /api/v1/animals: animals of the farmer, to restore them (HU13)."""

from fastapi import APIRouter, Depends, Query

from bovi.iam.interfaces.acl.iam_context_facade import AuthenticatedUserId
from bovi.livestock.application.internal.queryservices.animal_query_service import (
    AnimalQueryService,
)
from bovi.livestock.domain.model.queries.get_animals_query import GetAnimalsQuery
from bovi.livestock.interfaces.rest.dependencies import get_animal_query_service
from bovi.livestock.interfaces.rest.resources.animal_resources import AnimalPageResource
from bovi.livestock.interfaces.rest.transform.animal_assemblers import to_animal_page_resource
from bovi.shared.domain.model.valueobjects.page import DEFAULT_LIMIT
from bovi.shared.interfaces.rest.resources.error_resource import ErrorResource

router = APIRouter(tags=["Livestock"])


@router.get(
    "/animals",
    response_model=AnimalPageResource,
    summary="Animales del ganadero",
    description=(
        "Para restaurar el historial en un celular nuevo: restaure primero los animales y después "
        "las evaluaciones, que los referencian por `animal_id`. Ordenados por arete."
    ),
    responses={401: {"model": ErrorResource}, 422: {"model": ErrorResource}},
)
def list_animals(
    user_id: AuthenticatedUserId,
    limit: int = Query(DEFAULT_LIMIT, description="Entre 1 y 100"),
    cursor: str | None = Query(None, description="`next_cursor` de la página anterior"),
    service: AnimalQueryService = Depends(get_animal_query_service),
) -> AnimalPageResource:
    page = service.get_animals(GetAnimalsQuery(user_id=user_id, limit=limit, cursor=cursor))
    return to_animal_page_resource(page)

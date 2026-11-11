"""Health check used by Nginx and by the monitoring of the pilot (RNF15)."""

import logging

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.exc import SQLAlchemyError

from bovi import __version__
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import (
    Database,
    get_database,
)
from bovi.shared.interfaces.rest.resources.health_resource import HealthResource

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Salud"])


@router.get(
    "/health",
    response_model=HealthResource,
    summary="Estado del servicio y de la base de datos",
    responses={503: {"model": HealthResource, "description": "PostgreSQL no responde"}},
)
def health(response: Response, database: Database = Depends(get_database)) -> HealthResource:
    try:
        database.ping()
    except SQLAlchemyError:
        logger.warning("Health check: database is not reachable", exc_info=True)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResource(status="error", database="error", version=__version__)
    return HealthResource(status="ok", database="ok", version=__version__)

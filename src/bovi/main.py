"""Entry point of the modular monolith.

Each bounded context (iam, livestock, clinical) exposes its own routers under
/api/v1; they are registered here as they are built.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from bovi import __version__
from bovi.clinical.interfaces.rest import (
    evaluation_history_controller,
    evaluation_sync_controller,
    media_controller,
)
from bovi.iam.interfaces.rest import auth_controller
from bovi.livestock.interfaces.rest import animal_controller, animal_sync_controller
from bovi.shared.infrastructure.configuration.settings import Settings, get_settings
from bovi.shared.infrastructure.documentation.openapi.configuration.openapi_configuration import (
    openapi_options,
)
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Database
from bovi.shared.interfaces.rest import health_controller
from bovi.shared.interfaces.rest.error_handlers import register_error_handlers
from bovi.shared.interfaces.rest.security_headers import SecurityHeadersMiddleware

API_V1_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = settings
        app.state.database = Database(settings)
        yield
        app.state.database.dispose()

    app = FastAPI(version=__version__, lifespan=lifespan, **openapi_options(settings))
    app.add_middleware(SecurityHeadersMiddleware)
    register_error_handlers(app)
    app.include_router(health_controller.router)
    for router in (
        auth_controller.router,
        animal_sync_controller.router,
        animal_controller.router,
        media_controller.router,
        evaluation_sync_controller.router,
        evaluation_history_controller.router,
    ):
        app.include_router(router, prefix=API_V1_PREFIX)
    return app


def app_factory() -> FastAPI:
    """Used by `uvicorn --factory bovi.main:app_factory`."""
    return create_app()

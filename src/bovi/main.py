"""Entry point of the modular monolith.

Each bounded context (iam, livestock, clinical) exposes its own routers under
/api/v1; they are registered here as they are built.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from bovi import __version__
from bovi.shared.infrastructure.configuration.settings import Settings, get_settings
from bovi.shared.infrastructure.documentation.openapi.configuration.openapi_configuration import (
    openapi_options,
)
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Database
from bovi.shared.interfaces.rest import health_controller
from bovi.shared.interfaces.rest.error_handlers import register_error_handlers

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
    register_error_handlers(app)
    app.include_router(health_controller.router)
    return app


def app_factory() -> FastAPI:
    """Used by `uvicorn --factory bovi.main:app_factory`."""
    return create_app()

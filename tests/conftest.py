"""Shared fixtures.

Unit tests need nothing. Tests marked `integration` need PostgreSQL:

    docker compose up -d db

They use the `bovi_test` database (TEST_DATABASE_URL). Locally they are skipped
when PostgreSQL is down; in CI (CI=true) they fail instead, so they never stop
running unnoticed.
"""

import os
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from bovi.main import create_app
from bovi.shared.infrastructure.configuration.settings import Environment, Settings
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Database

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://bovi:bovi@localhost:5432/bovi_test"
)
TEST_JWT_SECRET = "secreto-de-pruebas-con-mas-de-32-caracteres"


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env=Environment.TEST,
        database_url=TEST_DATABASE_URL,
        jwt_secret=TEST_JWT_SECRET,
        s3_endpoint_url=None,
    )


@pytest.fixture(scope="session")
def database(settings: Settings) -> Iterator[Database]:
    """PostgreSQL for integration tests."""
    db = Database(settings)
    try:
        db.ping()
    except OperationalError:
        db.dispose()
        message = (
            f"PostgreSQL no disponible en {TEST_DATABASE_URL}: levante `docker compose up -d db`."
        )
        if os.environ.get("CI"):
            pytest.fail(message, pytrace=False)
        pytest.skip(message)
    yield db
    db.dispose()


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    # raise_server_exceptions=False: check the 500 response instead of the raised error.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client

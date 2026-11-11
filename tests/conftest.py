"""Shared fixtures.

Unit tests need nothing. Tests marked `integration` need PostgreSQL:

    docker compose up -d db

They use the `bovi_test` database (TEST_DATABASE_URL), migrated to head once per
run; the `db` fixture empties every table after each test. Locally they are skipped
when PostgreSQL is down; in CI (CI=true) they fail instead, so they never stop
running unnoticed.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

import bovi.iam.infrastructure.persistence.sqlalchemy.entities  # noqa: F401  (registers tables)
from bovi.main import create_app
from bovi.shared.infrastructure.configuration.settings import Environment, Settings
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import (
    Base,
    Database,
)

ROOT = Path(__file__).resolve().parents[1]

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
        bcrypt_rounds=4,
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
    command.upgrade(alembic_config(), "head")
    yield db
    db.dispose()


def alembic_config() -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL.replace("%", "%%"))
    return config


@pytest.fixture
def db(database: Database) -> Iterator[Database]:
    """Migrated PostgreSQL that is left empty after the test."""
    yield database
    tables = ", ".join(table.name for table in reversed(Base.metadata.sorted_tables))
    if tables:
        with database.engine.begin() as connection:
            connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    # raise_server_exceptions=False: check the 500 response instead of the raised error.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client

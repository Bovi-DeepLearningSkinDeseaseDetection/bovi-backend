import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from bovi import __version__
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import (
    Database,
    get_database,
)


class _UnreachableDatabase:
    def ping(self) -> None:
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))


@pytest.mark.integration
def test_health_is_ok_when_database_responds(client: TestClient, database: Database) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "version": __version__}


def test_health_is_503_when_database_is_down(app: FastAPI, client: TestClient) -> None:
    app.dependency_overrides[get_database] = _UnreachableDatabase

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "error"
    assert response.json()["database"] == "error"


def test_health_needs_no_token(app: FastAPI, client: TestClient) -> None:
    app.dependency_overrides[get_database] = _UnreachableDatabase

    response = client.get("/health")

    assert response.status_code != 401

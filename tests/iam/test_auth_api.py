"""HU14 - Registrarse e iniciar sesión, over the real API and PostgreSQL."""

from typing import Any
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from bovi.iam.infrastructure.persistence.sqlalchemy.entities.user_entity import UserEntity
from bovi.iam.interfaces.acl.iam_context_facade import AuthenticatedUserId
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Database

pytestmark = pytest.mark.integration

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
WRONG_CREDENTIALS = "Correo o contraseña incorrectos"


def _sign_up(client: TestClient, **overrides: Any):
    body = {
        "name": "Juan Pérez",
        "email": "juan.perez@example.com",
        "password": "establo2026",
        "consent_accepted": True,
    }
    body.update(overrides)
    return client.post(REGISTER, json=body)


def _user_row(db: Database, email: str) -> UserEntity | None:
    with db.session_factory() as session:
        return session.scalar(select(UserEntity).where(UserEntity.correo == email))


# --- Escenario 1: registro ---


def test_sign_up_creates_the_account_and_opens_the_session(
    client: TestClient, db: Database
) -> None:
    response = _sign_up(client)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 3600
    assert body["refresh_expires_in"] == 30 * 24 * 3600
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["name"] == "Juan Pérez"
    assert body["user"]["email"] == "juan.perez@example.com"
    assert "password" not in str(body)


def test_sign_up_stores_a_bcrypt_hash_and_the_consent(client: TestClient, db: Database) -> None:
    _sign_up(client, email="  Juan.Perez@Example.com ")

    row = _user_row(db, "juan.perez@example.com")
    assert row is not None
    assert row.hash_contrasena.startswith("$2b$")
    assert "establo2026" not in row.hash_contrasena
    assert row.consentimiento_aceptado_en is not None
    assert row.consentimiento_version == "2026.1"
    assert row.activo


def test_sign_up_without_consent_is_rejected(client: TestClient, db: Database) -> None:
    response = _sign_up(client, consent_accepted=False)

    assert response.status_code == 422
    assert response.json()["code"] == "consentimiento_requerido"
    assert _user_row(db, "juan.perez@example.com") is None


def test_sign_up_with_a_taken_email_is_a_conflict(client: TestClient, db: Database) -> None:
    _sign_up(client)

    response = _sign_up(client, email="JUAN.PEREZ@example.com", name="Otro Nombre")

    assert response.status_code == 409
    assert response.json()["code"] == "correo_registrado"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("email", "no-es-correo", "correo_invalido"),
        ("password", "corta1", "contrasena_debil"),
        ("password", "sinnumeros", "contrasena_debil"),
        ("name", "J", "nombre_invalido"),
    ],
)
def test_sign_up_validates_the_data(
    client: TestClient, db: Database, field: str, value: str, code: str
) -> None:
    response = _sign_up(client, **{field: value})

    assert response.status_code == 422
    assert response.json()["code"] == code


def test_sign_up_without_fields_lists_them_in_spanish(client: TestClient, db: Database) -> None:
    response = client.post(REGISTER, json={})

    assert response.status_code == 422
    fields = {d["field"]: d["message"] for d in response.json()["details"]}
    assert fields == {
        "name": "Este campo es obligatorio.",
        "email": "Este campo es obligatorio.",
        "password": "Este campo es obligatorio.",
        "consent_accepted": "Este campo es obligatorio.",
    }


# --- Escenario 2: inicio de sesión ---


def test_sign_in_with_correct_credentials(client: TestClient, db: Database) -> None:
    user_id = _sign_up(client).json()["user"]["id"]

    response = client.post(
        LOGIN, json={"email": "Juan.Perez@example.com", "password": "establo2026"}
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == user_id
    assert response.json()["access_token"]


# --- Escenario 3: credenciales incorrectas ---


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("juan.perez@example.com", "otraClave99"),
        ("nadie@example.com", "establo2026"),
        ("no-es-correo", "establo2026"),
    ],
)
def test_wrong_credentials_give_the_same_message(
    client: TestClient, db: Database, email: str, password: str
) -> None:
    _sign_up(client)

    response = client.post(LOGIN, json={"email": email, "password": password})

    assert response.status_code == 401
    assert response.json()["message"] == WRONG_CREDENTIALS
    assert response.headers["www-authenticate"] == "Bearer"


def test_deactivated_account_cannot_sign_in(client: TestClient, db: Database) -> None:
    _sign_up(client)
    with db.session_factory() as session:
        session.execute(update(UserEntity).values(activo=False))
        session.commit()

    response = client.post(
        LOGIN, json={"email": "juan.perez@example.com", "password": "establo2026"}
    )

    assert response.status_code == 403
    assert response.json()["code"] == "cuenta_desactivada"


# --- Escenario 4: la sesión dura 30 días (refresh token) ---


def test_refresh_token_renews_the_session(client: TestClient, db: Database) -> None:
    session = _sign_up(client).json()

    response = client.post(REFRESH, json={"refresh_token": session["refresh_token"]})

    assert response.status_code == 200
    assert response.json()["user"]["id"] == session["user"]["id"]
    assert response.json()["access_token"] != session["access_token"]


def test_access_token_cannot_be_used_to_refresh(client: TestClient, db: Database) -> None:
    session = _sign_up(client).json()

    response = client.post(REFRESH, json={"refresh_token": session["access_token"]})

    assert response.status_code == 401
    assert response.json()["code"] == "token_invalido"


# --- Rutas protegidas de los otros contextos (RNF5: sin token -> 401) ---


@pytest.fixture
def protected_client(app: FastAPI, client: TestClient) -> TestClient:
    @app.get("/api/v1/test/me")
    def me(user_id: AuthenticatedUserId) -> dict[str, str]:
        return {"user_id": str(user_id)}

    return client


def test_protected_route_without_token_is_401(protected_client: TestClient, db: Database) -> None:
    response = protected_client.get("/api/v1/test/me")

    assert response.status_code == 401
    assert response.json()["message"] == "Necesita iniciar sesión para continuar."


def test_protected_route_with_garbage_token_is_401(
    protected_client: TestClient, db: Database
) -> None:
    response = protected_client.get(
        "/api/v1/test/me", headers={"Authorization": "Bearer abc.def.ghi"}
    )

    assert response.status_code == 401
    assert response.json()["code"] == "token_invalido"


def test_protected_route_rejects_the_refresh_token(
    protected_client: TestClient, db: Database
) -> None:
    session = _sign_up(protected_client).json()

    response = protected_client.get(
        "/api/v1/test/me", headers={"Authorization": f"Bearer {session['refresh_token']}"}
    )

    assert response.status_code == 401


def test_protected_route_gets_the_user_from_the_token(
    protected_client: TestClient, db: Database
) -> None:
    session = _sign_up(protected_client).json()

    response = protected_client.get(
        "/api/v1/test/me", headers={"Authorization": f"Bearer {session['access_token']}"}
    )

    assert response.status_code == 200
    assert UUID(response.json()["user_id"]) == UUID(session["user"]["id"])


def test_protected_route_rejects_a_deactivated_account(
    protected_client: TestClient, db: Database
) -> None:
    session = _sign_up(protected_client).json()
    with db.session_factory() as s:
        s.execute(update(UserEntity).values(activo=False))
        s.commit()

    response = protected_client.get(
        "/api/v1/test/me", headers={"Authorization": f"Bearer {session['access_token']}"}
    )

    assert response.status_code == 403

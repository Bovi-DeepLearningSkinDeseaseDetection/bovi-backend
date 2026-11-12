"""Every error reaches the app as an ErrorResource with a message in Spanish."""

from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, field_validator

from bovi.shared.domain.exceptions import (
    AuthenticationError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from bovi.shared.interfaces.rest.error_handlers import register_error_handlers


class _Item(BaseModel):
    uuid: UUID
    ear_tag: str = Field(min_length=1, max_length=20)

    @field_validator("ear_tag")
    @classmethod
    def _upper_case(cls, value: str) -> str:
        if value != value.upper():
            raise ValueError("El arete debe estar en mayúsculas.")
        return value


class _Batch(BaseModel):
    items: list[_Item] = Field(max_length=2)


def _build_app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    errors: dict[str, DomainError] = {
        "validation": ValidationError("La zona corporal no es válida."),
        "not-found": NotFoundError("El animal no existe."),
        "conflict": ConflictError("Ya existe un animal con ese arete.", code="arete_duplicado"),
        "authentication": AuthenticationError("Correo o contraseña incorrectos"),
        "permission": PermissionDeniedError("No puede ver datos de otro ganadero."),
        "generic": DomainError("La evaluación no se puede modificar."),
    }

    @app.get("/domain/{kind}")
    def raise_domain_error(kind: str) -> None:
        raise errors[kind]

    @app.post("/batch")
    def receive_batch(batch: _Batch) -> dict[str, int]:
        return {"count": len(batch.items)}

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret internal detail")

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_build_app(), raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("kind", "status_code", "code", "message"),
    [
        ("validation", 422, "datos_invalidos", "La zona corporal no es válida."),
        ("not-found", 404, "no_encontrado", "El animal no existe."),
        ("conflict", 409, "arete_duplicado", "Ya existe un animal con ese arete."),
        ("authentication", 401, "no_autenticado", "Correo o contraseña incorrectos"),
        ("permission", 403, "sin_permiso", "No puede ver datos de otro ganadero."),
        ("generic", 400, "regla_de_negocio", "La evaluación no se puede modificar."),
    ],
)
def test_domain_errors_map_to_http_status(
    client: TestClient, kind: str, status_code: int, code: str, message: str
) -> None:
    response = client.get(f"/domain/{kind}")

    assert response.status_code == status_code
    assert response.json() == {"code": code, "message": message, "details": []}


def test_authentication_error_asks_for_bearer_token(client: TestClient) -> None:
    response = client.get("/domain/authentication")

    assert response.headers["www-authenticate"] == "Bearer"


def test_invalid_body_lists_each_field_in_spanish(client: TestClient) -> None:
    body = {"items": [{"uuid": "no-es-uuid", "ear_tag": ""}, {"ear_tag": "pe-01"}]}

    response = client.post("/batch", json=body)

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "datos_invalidos"
    assert payload["message"] == "Algunos datos enviados no son válidos."
    assert {(d["field"], d["message"]) for d in payload["details"]} == {
        ("items[0].uuid", "Debe ser un UUID válido."),
        ("items[0].ear_tag", "Debe tener al menos 1 carácter."),
        ("items[1].uuid", "Este campo es obligatorio."),
        ("items[1].ear_tag", "El arete debe estar en mayúsculas."),
    }


def test_too_many_items_is_reported(client: TestClient) -> None:
    item = {"uuid": "6f1c2a7e-9d4b-4c1a-8f00-000000000001", "ear_tag": "PE-01"}

    response = client.post("/batch", json={"items": [item, item, item]})

    assert response.status_code == 422
    assert response.json()["details"] == [
        {"field": "items", "message": "Debe tener como máximo 2 elementos."}
    ]


def test_malformed_json_is_reported(client: TestClient) -> None:
    response = client.post(
        "/batch", content="{no es json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422
    assert response.json()["details"][0]["message"] == (
        "El cuerpo de la solicitud no es un JSON válido."
    )


def test_unknown_route_is_404_in_spanish(client: TestClient) -> None:
    response = client.get("/no-existe")

    assert response.status_code == 404
    assert response.json() == {
        "code": "no_encontrado",
        "message": "El recurso solicitado no existe.",
        "details": [],
    }


def test_wrong_method_is_405_in_spanish(client: TestClient) -> None:
    response = client.delete("/batch")

    assert response.status_code == 405
    assert response.json()["code"] == "metodo_no_permitido"


def test_unexpected_error_hides_internal_details(client: TestClient) -> None:
    response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {
        "code": "error_interno",
        "message": "Ocurrió un error inesperado. Intente de nuevo más tarde.",
        "details": [],
    }
    assert "secret" not in response.text


def test_body_that_is_not_utf8_is_400_in_spanish(client: TestClient) -> None:
    body = '{"items": [], "nombre": "P\xe9rez"}'.encode("latin-1")

    response = client.post("/batch", content=body, headers={"Content-Type": "application/json"})

    assert response.status_code in (400, 422)
    assert "error parsing" not in response.text
    assert response.json()["message"] in (
        "La solicitud no es válida.",
        "Algunos datos enviados no son válidos.",
    )

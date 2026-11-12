"""HU12 - Sincronizar automáticamente las evaluaciones (API + PostgreSQL, S3 simulado)."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from bovi.clinical.domain.model.valueobjects.image_key import image_key_for
from bovi.clinical.infrastructure.persistence.sqlalchemy.entities.evaluation_entity import (
    EvaluationEntity,
)
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Database
from tests.clinical.builders import animal, evaluation, healthy, inconclusive
from tests.conftest import Farmer, sign_up
from tests.fakes import FakeImageStorage

pytestmark = pytest.mark.integration

URL = "/api/v1/sync/evaluations"


def _count(db: Database) -> int:
    with db.session_factory() as session:
        return session.scalar(select(func.count()).select_from(EvaluationEntity))


def _upload(storage: FakeImageStorage, farmer: Farmer, *bodies: dict) -> None:
    for body in bodies:
        storage.put(image_key_for(farmer.id, UUID(body["id"])))


def _sync_animal(client: TestClient, farmer: Farmer, **overrides) -> UUID:
    body = animal(**overrides)
    response = client.post("/api/v1/sync/animals", json={"animals": [body]}, headers=farmer.headers)
    assert response.json()["results"][0]["status"] == "accepted"
    return UUID(body["id"])


# --- Escenarios 1 y 2: se guarda y el servidor confirma la recepción ---


def test_evaluations_with_their_photo_are_accepted(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    animal_id = _sync_animal(client, farmer)
    batch = [evaluation(animal_id=animal_id), healthy(), inconclusive()]
    _upload(storage, farmer, *batch)

    response = client.post(URL, json={"evaluations": batch}, headers=farmer.headers)

    assert response.status_code == 200
    body = response.json()
    assert [r["status"] for r in body["results"]] == ["accepted"] * 3
    assert body["accepted"] == 3
    assert _count(db) == 3


def test_the_row_keeps_the_full_result(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    animal_id = _sync_animal(client, farmer)
    body = evaluation(animal_id=animal_id)
    _upload(storage, farmer, body)

    client.post(URL, json={"evaluations": [body]}, headers=farmer.headers)

    with db.session_factory() as session:
        row = session.get(EvaluationEntity, UUID(body["id"]))
    assert row.usuario_id == farmer.id
    assert row.animal_id == animal_id
    assert row.zona_corporal == "flank"
    assert row.resultado == "lesion"
    assert row.clase_predicha == "sarna"
    assert row.version_modelo == "v7c_peso_pap"  # RNF17
    assert len(row.probabilidades) == 5
    assert row.codigos_clinicos[0] == {
        "system": "http://id.nlm.nih.gov/mesh",
        "code": "D008924",
        "display": "Mite Infestations",
    }
    assert row.origen_imagen == "camera"
    assert row.clave_imagen == f"evaluaciones/{farmer.id}/{body['id']}.jpg"


# --- Escenario 3: corte de conexión, reintento sin pérdidas ni duplicados ---


def test_resending_the_same_batch_duplicates_nothing(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    batch = [healthy(), healthy()]
    _upload(storage, farmer, *batch)
    client.post(URL, json={"evaluations": batch}, headers=farmer.headers)

    response = client.post(URL, json={"evaluations": batch}, headers=farmer.headers)

    assert [r["status"] for r in response.json()["results"]] == ["duplicate", "duplicate"]
    assert _count(db) == 2


def test_a_resent_evaluation_is_not_modified(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    body = healthy()
    _upload(storage, farmer, body)
    client.post(URL, json={"evaluations": [body]}, headers=farmer.headers)
    changed = {**body, "model_version": "otra"}

    client.post(URL, json={"evaluations": [changed]}, headers=farmer.headers)

    with db.session_factory() as session:
        assert session.get(EvaluationEntity, UUID(body["id"])).version_modelo == "v7c_peso_pap"


def test_the_same_id_twice_in_a_batch_is_saved_once(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    body = healthy()
    _upload(storage, farmer, body)

    results = client.post(URL, json={"evaluations": [body, body]}, headers=farmer.headers).json()

    assert [r["status"] for r in results["results"]] == ["accepted", "duplicate"]
    assert _count(db) == 1


def test_a_partial_batch_can_be_completed_later(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    # The connection dropped after the first photo was uploaded.
    farmer = sign_up(client)
    first, second = healthy(), evaluation()
    _upload(storage, farmer, first)

    results = client.post(URL, json={"evaluations": [first, second]}, headers=farmer.headers)
    assert [r["status"] for r in results.json()["results"]] == ["accepted", "rejected"]
    assert results.json()["results"][1]["code"] == "imagen_no_encontrada"

    _upload(storage, farmer, second)
    retry = client.post(URL, json={"evaluations": [first, second]}, headers=farmer.headers)

    assert [r["status"] for r in retry.json()["results"]] == ["duplicate", "accepted"]
    assert _count(db) == 2


# --- Escenario 4: seguridad ---


def test_sync_needs_a_session(client: TestClient, db: Database, storage: FakeImageStorage) -> None:
    response = client.post(URL, json={"evaluations": [healthy()]})

    assert response.status_code == 401


def test_the_photo_must_be_under_the_farmers_own_key(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    juan = sign_up(client, "juan@example.com")
    rosa = sign_up(client, "rosa@example.com")
    body = healthy()
    _upload(storage, juan, body)  # Juan's photo; Rosa tries to claim it.

    result = client.post(URL, json={"evaluations": [body]}, headers=rosa.headers).json()

    assert result["results"][0]["code"] == "imagen_no_encontrada"


def test_an_id_of_another_farmer_is_rejected(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    juan = sign_up(client, "juan@example.com")
    rosa = sign_up(client, "rosa@example.com")
    body = healthy()
    _upload(storage, juan, body)
    _upload(storage, rosa, body)
    client.post(URL, json={"evaluations": [body]}, headers=juan.headers)

    result = client.post(URL, json={"evaluations": [body]}, headers=rosa.headers).json()

    assert result["results"][0]["status"] == "rejected"
    assert result["results"][0]["code"] == "id_en_uso"


def test_the_animal_must_be_synced_and_owned(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    juan = sign_up(client, "juan@example.com")
    rosa = sign_up(client, "rosa@example.com")
    rosas_animal = _sync_animal(client, rosa)
    not_synced = evaluation(animal_id=uuid4())
    someone_elses = evaluation(animal_id=rosas_animal)
    _upload(storage, juan, not_synced, someone_elses)

    results = client.post(
        URL, json={"evaluations": [not_synced, someone_elses]}, headers=juan.headers
    ).json()["results"]

    assert [r["code"] for r in results] == ["animal_no_sincronizado", "animal_no_sincronizado"]


# --- Validación de cada registro ---


def test_a_photo_too_big_or_not_jpeg_is_rejected(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    big, png = healthy(), healthy()
    storage.put(image_key_for(farmer.id, UUID(big["id"])), size=900_000)
    storage.put(image_key_for(farmer.id, UUID(png["id"])), content_type="image/png")

    results = client.post(URL, json={"evaluations": [big, png]}, headers=farmer.headers).json()

    assert [r["code"] for r in results["results"]] == ["imagen_invalida", "imagen_invalida"]


def test_an_inconsistent_result_is_rejected_alone(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    bad = evaluation(confidence=0.5)
    good = healthy()
    _upload(storage, farmer, bad, good)

    results = client.post(URL, json={"evaluations": [bad, good]}, headers=farmer.headers).json()

    assert results["results"][0]["status"] == "rejected"
    assert results["results"][0]["code"] == "evaluacion_invalida"
    assert "confianza" in results["results"][0]["message"]
    assert results["results"][1]["status"] == "accepted"


def test_photos_are_only_checked_for_new_evaluations(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    batch = [healthy() for _ in range(3)]
    _upload(storage, farmer, *batch)
    client.post(URL, json={"evaluations": batch}, headers=farmer.headers)
    storage.head_calls = 0

    client.post(URL, json={"evaluations": batch}, headers=farmer.headers)

    assert storage.head_calls == 0


def test_batch_of_more_than_20_is_rejected(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)

    response = client.post(
        URL, json={"evaluations": [healthy() for _ in range(21)]}, headers=farmer.headers
    )

    assert response.status_code == 422
    assert response.json()["message"] == (
        "Envíe como máximo 20 registros de evaluaciones por solicitud."
    )


def test_unknown_enum_values_are_rejected_with_the_allowed_ones(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    body = {**healthy(), "outcome": "sano"}
    _upload(storage, farmer, body)

    result = client.post(URL, json={"evaluations": [body]}, headers=farmer.headers).json()

    assert result["results"][0]["code"] == "valor_invalido"
    assert result["results"][0]["message"] == (
        "El campo outcome debe ser uno de: healthy, lesion, inconclusive."
    )

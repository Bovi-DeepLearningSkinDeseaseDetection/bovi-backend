"""POST /api/v1/sync/animals: HU15 (arete único) + HU12 (sin pérdidas ni duplicados)."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from bovi.livestock.infrastructure.persistence.sqlalchemy.entities.animal_entity import (
    AnimalEntity,
)
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Database
from tests.clinical.builders import animal
from tests.conftest import sign_up

pytestmark = pytest.mark.integration

URL = "/api/v1/sync/animals"


def _count(db: Database) -> int:
    with db.session_factory() as session:
        return session.scalar(select(func.count()).select_from(AnimalEntity))


def test_new_animals_are_accepted_and_normalized(client: TestClient, db: Database) -> None:
    farmer = sign_up(client)
    a, b = animal(ear_tag="pe 0012"), animal(ear_tag="PE-0047", sex="male", breed="Jersey")

    response = client.post(URL, json={"animals": [a, b]}, headers=farmer.headers)

    assert response.status_code == 200
    body = response.json()
    assert [r["status"] for r in body["results"]] == ["accepted", "accepted"]
    assert body["accepted"] == 2
    with db.session_factory() as session:
        row = session.get(AnimalEntity, UUID(a["id"]))
        assert row.arete == "PE0012"
        assert row.usuario_id == farmer.id


def test_resending_the_batch_creates_no_copies(client: TestClient, db: Database) -> None:
    farmer = sign_up(client)
    batch = {"animals": [animal(), animal(ear_tag="PE-0047")]}
    client.post(URL, json=batch, headers=farmer.headers)

    response = client.post(URL, json=batch, headers=farmer.headers)

    assert [r["status"] for r in response.json()["results"]] == ["duplicate", "duplicate"]
    assert _count(db) == 2


def test_same_ear_tag_with_another_id_is_merged(client: TestClient, db: Database) -> None:
    # HU15, escenario 4: el arete es único por ganadero.
    farmer = sign_up(client)
    first = animal(ear_tag="PE-0012")
    client.post(URL, json={"animals": [first]}, headers=farmer.headers)
    second = animal(ear_tag="pe-0012")

    result = client.post(URL, json={"animals": [second]}, headers=farmer.headers).json()

    assert result["results"][0]["status"] == "merged"
    assert result["results"][0]["canonical_id"] == first["id"]
    assert _count(db) == 1


def test_same_ear_tag_twice_in_one_batch_is_merged(client: TestClient, db: Database) -> None:
    farmer = sign_up(client)
    a, b = animal(ear_tag="PE0012"), animal(ear_tag="pe 0012")

    results = client.post(URL, json={"animals": [a, b]}, headers=farmer.headers).json()["results"]

    assert results[0]["status"] == "accepted"
    assert results[1] == {
        "id": b["id"],
        "status": "merged",
        "canonical_id": a["id"],
        "code": None,
        "message": None,
    }


def test_two_farmers_can_use_the_same_ear_tag(client: TestClient, db: Database) -> None:
    juan = sign_up(client, "juan@example.com")
    rosa = sign_up(client, "rosa@example.com")

    client.post(URL, json={"animals": [animal(ear_tag="PE-0001")]}, headers=juan.headers)
    response = client.post(URL, json={"animals": [animal(ear_tag="PE-0001")]}, headers=rosa.headers)

    assert response.json()["results"][0]["status"] == "accepted"


def test_an_id_of_another_farmer_is_rejected(client: TestClient, db: Database) -> None:
    juan = sign_up(client, "juan@example.com")
    rosa = sign_up(client, "rosa@example.com")
    shared_id = str(uuid4())
    client.post(URL, json={"animals": [animal(id=shared_id)]}, headers=juan.headers)

    result = client.post(
        URL, json={"animals": [animal(id=shared_id, ear_tag="RS-1")]}, headers=rosa.headers
    ).json()["results"][0]

    assert result["status"] == "rejected"
    assert result["code"] == "id_en_uso"


def test_an_invalid_animal_does_not_block_the_rest(client: TestClient, db: Database) -> None:
    farmer = sign_up(client)
    bad = animal(ear_tag="PE_01", sex="hembra")
    good = animal(ear_tag="PE-0002")

    results = client.post(URL, json={"animals": [bad, good]}, headers=farmer.headers).json()

    assert results["results"][0]["status"] == "rejected"
    assert results["results"][0]["code"] == "arete_invalido"
    assert results["results"][0]["message"] == "Use solo letras, números y guiones."
    assert results["results"][1]["status"] == "accepted"
    assert results["rejected"] == 1


def test_batch_limits(client: TestClient, db: Database) -> None:
    farmer = sign_up(client)

    empty = client.post(URL, json={"animals": []}, headers=farmer.headers)
    too_many = client.post(
        URL,
        json={"animals": [animal(ear_tag=f"PE-{i}") for i in range(51)]},
        headers=farmer.headers,
    )

    assert empty.status_code == 422
    assert empty.json()["code"] == "lote_vacio"
    assert too_many.status_code == 422
    assert too_many.json()["code"] == "lote_muy_grande"


def test_sync_needs_a_session(client: TestClient, db: Database) -> None:
    response = client.post(URL, json={"animals": [animal()]})

    assert response.status_code == 401
    assert _count(db) == 0

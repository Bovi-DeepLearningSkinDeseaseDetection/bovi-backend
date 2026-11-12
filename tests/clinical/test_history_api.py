"""HU13 - Restaurar el historial en un nuevo dispositivo (API + PostgreSQL, S3 simulado)."""

import time
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from bovi.clinical.domain.model.valueobjects.image_key import image_key_for
from bovi.shared.domain.model.valueobjects.page import encode_cursor
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Database
from tests.clinical.builders import animal, evaluation, healthy, inconclusive
from tests.conftest import Farmer, sign_up
from tests.fakes import FakeImageStorage

pytestmark = pytest.mark.integration

EVALUATIONS = "/api/v1/evaluations"
ANIMALS = "/api/v1/animals"
START = datetime(2026, 11, 1, 8, 0, tzinfo=UTC)


def _sync(
    client: TestClient, storage: FakeImageStorage, farmer: Farmer, bodies: list[dict]
) -> None:
    for start in range(0, len(bodies), 20):
        batch = bodies[start : start + 20]
        for body in batch:
            storage.put(image_key_for(farmer.id, UUID(body["id"])))
        response = client.post(
            "/api/v1/sync/evaluations", json={"evaluations": batch}, headers=farmer.headers
        )
        assert response.json()["accepted"] == len(batch), response.text


def _at(minutes: int) -> str:
    return (START + timedelta(minutes=minutes)).isoformat()


def _all_pages(client: TestClient, farmer: Farmer, url: str, limit: int) -> list[dict]:
    items, cursor = [], None
    while True:
        params = {"limit": limit, **({"cursor": cursor} if cursor else {})}
        page = client.get(url, params=params, headers=farmer.headers).json()
        items += page["items"]
        cursor = page["next_cursor"]
        if cursor is None:
            return items


# --- Escenario 1: restauración ---


def test_history_restores_every_field_and_the_photo_url(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    animal_body = animal(ear_tag="PE-0047")
    client.post("/api/v1/sync/animals", json={"animals": [animal_body]}, headers=farmer.headers)
    sent = evaluation(animal_id=UUID(animal_body["id"]), evaluated_at=_at(0))
    _sync(client, storage, farmer, [sent])

    page = client.get(EVALUATIONS, headers=farmer.headers).json()

    assert page["total"] == 1
    assert page["next_cursor"] is None
    item = page["items"][0]
    restored = {k: item[k] for k in sent if k != "evaluated_at"}
    assert restored == {k: v for k, v in sent.items() if k != "evaluated_at"}
    assert datetime.fromisoformat(item["evaluated_at"]) == datetime.fromisoformat(
        sent["evaluated_at"]
    )
    assert f"evaluaciones/{farmer.id}/{sent['id']}.jpg" in item["image_url"]
    assert item["image_url_expires_in"] == 900


def test_animals_are_restored_too(client: TestClient, db: Database) -> None:
    farmer = sign_up(client)
    bodies = [animal(ear_tag=tag) for tag in ("PE-0003", "PE-0001", "PE-0002")]
    client.post("/api/v1/sync/animals", json={"animals": bodies}, headers=farmer.headers)

    page = client.get(ANIMALS, headers=farmer.headers).json()

    assert page["total"] == 3
    assert [a["ear_tag"] for a in page["items"]] == ["PE-0001", "PE-0002", "PE-0003"]
    assert page["items"][0] == {
        "id": bodies[1]["id"],
        "ear_tag": "PE-0001",
        "breed": "Holstein",
        "sex": "female",
        "created_at": page["items"][0]["created_at"],
    }


def test_newest_first_and_every_page_without_gaps_or_repeats(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    # Two evaluations at the same instant: the id breaks the tie.
    bodies = [healthy(evaluated_at=_at(i)) for i in range(45)]
    bodies += [inconclusive(evaluated_at=_at(10)) for _ in range(2)]
    _sync(client, storage, farmer, bodies)

    items = _all_pages(client, farmer, EVALUATIONS, limit=10)

    assert len(items) == 47
    assert len({i["id"] for i in items}) == 47
    dates = [datetime.fromisoformat(i["evaluated_at"]) for i in items]
    assert dates == sorted(dates, reverse=True)


def test_animal_pages_follow_the_cursor(client: TestClient, db: Database) -> None:
    farmer = sign_up(client)
    client.post(
        "/api/v1/sync/animals",
        json={"animals": [animal(ear_tag=f"PE-{i:03}") for i in range(23)]},
        headers=farmer.headers,
    )

    items = _all_pages(client, farmer, ANIMALS, limit=5)

    assert [a["ear_tag"] for a in items] == [f"PE-{i:03}" for i in range(23)]


def test_new_evaluations_while_restoring_do_not_shift_the_pages(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    _sync(client, storage, farmer, [healthy(evaluated_at=_at(i)) for i in range(6)])
    first = client.get(EVALUATIONS, params={"limit": 3}, headers=farmer.headers).json()
    # The old phone syncs a newer evaluation in the middle of the restore.
    _sync(client, storage, farmer, [healthy(evaluated_at=_at(100))])

    second = client.get(
        EVALUATIONS, params={"limit": 3, "cursor": first["next_cursor"]}, headers=farmer.headers
    ).json()

    seen = {i["id"] for i in first["items"]} | {i["id"] for i in second["items"]}
    assert len(seen) == 6


# --- Escenario 2: 200 evaluaciones en 2 minutos o menos ---


def test_200_evaluations_are_restored_in_a_few_requests(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    _sync(client, storage, farmer, [healthy(evaluated_at=_at(i)) for i in range(200)])

    started = time.perf_counter()
    items = _all_pages(client, farmer, EVALUATIONS, limit=100)
    elapsed = time.perf_counter() - started

    assert len(items) == 200
    assert all(i["image_url"] for i in items)
    # The backend part is a small slice of the 2 minutes; the rest is downloading the photos.
    assert elapsed < 5


# --- Escenario 3: solo sus datos ---


def test_each_farmer_only_gets_their_own_data(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    juan = sign_up(client, "juan@example.com")
    rosa = sign_up(client, "rosa@example.com")
    _sync(client, storage, juan, [healthy(evaluated_at=_at(i)) for i in range(3)])
    _sync(client, storage, rosa, [healthy(evaluated_at=_at(i)) for i in range(2)])
    client.post("/api/v1/sync/animals", json={"animals": [animal()]}, headers=juan.headers)

    rosas = client.get(EVALUATIONS, headers=rosa.headers).json()
    rosas_animals = client.get(ANIMALS, headers=rosa.headers).json()

    assert rosas["total"] == 2
    assert all(f"evaluaciones/{rosa.id}/" in i["image_url"] for i in rosas["items"])
    assert rosas_animals == {"items": [], "total": 0, "next_cursor": None}


def test_a_cursor_cannot_be_used_to_read_another_farmer(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    juan = sign_up(client, "juan@example.com")
    rosa = sign_up(client, "rosa@example.com")
    _sync(client, storage, juan, [healthy(evaluated_at=_at(i)) for i in range(4)])
    juans_cursor = client.get(EVALUATIONS, params={"limit": 2}, headers=juan.headers).json()[
        "next_cursor"
    ]

    page = client.get(EVALUATIONS, params={"cursor": juans_cursor}, headers=rosa.headers).json()

    assert page["items"] == []


def test_history_needs_a_session(client: TestClient, db: Database) -> None:
    assert client.get(EVALUATIONS).status_code == 401
    assert client.get(ANIMALS).status_code == 401


# --- Parámetros ---


@pytest.mark.parametrize(
    "cursor",
    ["no-es-un-cursor", encode_cursor({"at": "ayer", "id": "x"}), encode_cursor({"tag": 5})],
)
def test_invalid_cursor_is_422_in_spanish(
    client: TestClient, db: Database, storage: FakeImageStorage, cursor: str
) -> None:
    farmer = sign_up(client)

    for url in (EVALUATIONS, ANIMALS):
        response = client.get(url, params={"cursor": cursor}, headers=farmer.headers)
        assert response.status_code == 422, (url, cursor)
        assert response.json()["code"] == "cursor_invalido"


@pytest.mark.parametrize("limit", [0, 101])
def test_limit_must_be_between_1_and_100(
    client: TestClient, db: Database, storage: FakeImageStorage, limit: int
) -> None:
    farmer = sign_up(client)

    response = client.get(EVALUATIONS, params={"limit": limit}, headers=farmer.headers)

    assert response.status_code == 422
    assert response.json()["message"] == "El límite debe estar entre 1 y 100."

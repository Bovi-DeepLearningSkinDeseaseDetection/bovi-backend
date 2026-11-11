"""POST /api/v1/media/upload-url y /download-url (RNF18, HU12 escenario 4)."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from bovi.clinical.domain.model.valueobjects.image_key import image_key_for
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Database
from tests.clinical.builders import healthy
from tests.conftest import sign_up
from tests.fakes import FakeImageStorage

pytestmark = pytest.mark.integration

UPLOAD = "/api/v1/media/upload-url"
DOWNLOAD = "/api/v1/media/download-url"
SYNC = "/api/v1/sync/evaluations"


def test_upload_url_uses_the_farmers_own_key(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    evaluation_id = uuid4()

    response = client.post(
        UPLOAD, json={"evaluation_ids": [str(evaluation_id)]}, headers=farmer.headers
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["status"] == "ready"
    assert item["image_key"] == f"evaluaciones/{farmer.id}/{evaluation_id}.jpg"
    assert item["upload"]["fields"]["key"] == item["image_key"]
    assert item["upload"]["max_bytes"] == 512_000
    assert item["upload"]["expires_in"] == 900


def test_no_upload_url_for_an_evaluation_already_synced(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    farmer = sign_up(client)
    body = healthy()
    storage.put(image_key_for(farmer.id, UUID(body["id"])))
    client.post(SYNC, json={"evaluations": [body]}, headers=farmer.headers)

    item = client.post(
        UPLOAD, json={"evaluation_ids": [body["id"]]}, headers=farmer.headers
    ).json()["items"][0]

    assert item == {
        "evaluation_id": body["id"],
        "status": "already_synced",
        "image_key": None,
        "upload": None,
    }


def test_download_url_only_for_own_synced_evaluations(
    client: TestClient, db: Database, storage: FakeImageStorage
) -> None:
    juan = sign_up(client, "juan@example.com")
    rosa = sign_up(client, "rosa@example.com")
    body = healthy()
    storage.put(image_key_for(juan.id, UUID(body["id"])))
    client.post(SYNC, json={"evaluations": [body]}, headers=juan.headers)
    unknown = str(uuid4())

    juans = client.post(
        DOWNLOAD, json={"evaluation_ids": [body["id"], unknown]}, headers=juan.headers
    ).json()["items"]
    rosas = client.post(
        DOWNLOAD, json={"evaluation_ids": [body["id"]]}, headers=rosa.headers
    ).json()["items"]

    assert juans[0]["status"] == "ready"
    assert f"evaluaciones/{juan.id}/{body['id']}.jpg" in juans[0]["url"]
    assert juans[1]["status"] == "not_found"
    # Rosa cannot tell that Juan's evaluation exists.
    assert rosas[0] == {
        "evaluation_id": body["id"],
        "status": "not_found",
        "url": None,
        "expires_in": None,
    }


def test_media_needs_a_session(client: TestClient, db: Database, storage: FakeImageStorage) -> None:
    response = client.post(UPLOAD, json={"evaluation_ids": [str(uuid4())]})

    assert response.status_code == 401


def test_media_batch_limits(client: TestClient, db: Database, storage: FakeImageStorage) -> None:
    farmer = sign_up(client)

    response = client.post(
        UPLOAD, json={"evaluation_ids": [str(uuid4()) for _ in range(21)]}, headers=farmer.headers
    )

    assert response.status_code == 422
    assert response.json()["code"] == "lote_muy_grande"

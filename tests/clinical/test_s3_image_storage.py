"""S3ImageStorage against a real S3 API (RustFS: `docker compose up -d s3 s3-init`).

Checks what a fake cannot: S3 itself enforces the policy of the presigned POST
(size and type, RNF18), and HeadObject sees the uploaded photo.
"""

import os
from collections.abc import Iterator
from uuid import uuid4

import boto3
import httpx
import pytest
from botocore.exceptions import BotoCoreError, ClientError

from bovi.clinical.infrastructure.storage.s3.services.s3_image_storage import S3ImageStorage
from bovi.shared.infrastructure.configuration.settings import Settings

pytestmark = [pytest.mark.integration, pytest.mark.s3]

ENDPOINT = os.environ.get("TEST_S3_ENDPOINT_URL", "http://localhost:9000")
BUCKET = "bovi-evaluaciones-test"
MAX_BYTES = 2048


@pytest.fixture(scope="module")
def storage(settings: Settings) -> Iterator[S3ImageStorage]:
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "bovilocal")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "bovilocal123")
    client = boto3.client("s3", endpoint_url=ENDPOINT, region_name="us-east-1")
    try:
        try:
            client.head_bucket(Bucket=BUCKET)
        except ClientError:
            client.create_bucket(Bucket=BUCKET)
    except (BotoCoreError, ClientError) as error:
        message = f"S3 no disponible en {ENDPOINT} ({error}): levante `docker compose up -d s3`."
        if os.environ.get("CI"):
            pytest.fail(message, pytrace=False)
        pytest.skip(message)
    yield S3ImageStorage(
        settings.model_copy(
            update={
                "s3_endpoint_url": ENDPOINT,
                "s3_bucket": BUCKET,
                "s3_max_image_bytes": MAX_BYTES,
            }
        )
    )


def _post(storage: S3ImageStorage, key: str, data: bytes, content_type: str = "image/jpeg"):
    upload = storage.presign_upload(key)
    fields = {**upload.fields, "Content-Type": content_type}
    return httpx.post(upload.url, data=fields, files={"file": ("foto.jpg", data, content_type)})


def test_a_jpeg_within_the_limit_is_uploaded_and_found(storage: S3ImageStorage) -> None:
    key = f"evaluaciones/{uuid4()}/{uuid4()}.jpg"
    photo = b"\xff\xd8\xff" + b"x" * 1000

    response = _post(storage, key, photo)

    assert response.status_code in (200, 201, 204)
    stat = storage.stat_many([key])[key]
    assert stat is not None
    assert stat.size == len(photo)
    assert stat.content_type == "image/jpeg"
    download = storage.presign_download(key)
    assert httpx.get(download.url).content == photo


def test_s3_rejects_a_photo_over_the_limit(storage: S3ImageStorage) -> None:
    key = f"evaluaciones/{uuid4()}/{uuid4()}.jpg"

    response = _post(storage, key, b"x" * (MAX_BYTES + 1))

    assert response.status_code == 400
    assert storage.stat_many([key]) == {key: None}


def test_s3_rejects_a_file_that_is_not_jpeg(storage: S3ImageStorage) -> None:
    key = f"evaluaciones/{uuid4()}/{uuid4()}.jpg"

    response = _post(storage, key, b"x" * 100, content_type="image/png")

    assert response.status_code in (400, 403)
    assert storage.stat_many([key]) == {key: None}


def test_stat_many_checks_several_keys_at_once(storage: S3ImageStorage) -> None:
    present = f"evaluaciones/{uuid4()}/{uuid4()}.jpg"
    _post(storage, present, b"x" * 10)
    missing = [f"evaluaciones/{uuid4()}/{uuid4()}.jpg" for _ in range(5)]

    stats = storage.stat_many([present, *missing])

    assert stats[present] is not None
    assert all(stats[key] is None for key in missing)

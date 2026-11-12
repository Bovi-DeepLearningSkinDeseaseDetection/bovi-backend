"""Photos of the evaluations in Amazon S3 (RustFS in local development)."""

import logging
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from bovi.clinical.domain.services.image_storage import (
    JPEG,
    PresignedDownload,
    PresignedUpload,
    StoredImage,
)
from bovi.shared.domain.exceptions import ServiceUnavailableError
from bovi.shared.infrastructure.configuration.settings import Settings

logger = logging.getLogger(__name__)

_MAX_PARALLEL_HEADS = 10


@lru_cache(maxsize=8)
def _client(endpoint_url: str | None, region: str) -> BaseClient:
    """boto3 clients are thread-safe and slow to build: one per endpoint for the process.

    Credentials come from the environment: the IAM role of the EC2 in AWS,
    AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY in local development.
    """
    config = Config(
        signature_version="s3v4",
        connect_timeout=2,
        read_timeout=5,
        retries={"max_attempts": 3, "mode": "standard"},
        # Emulators answer on one host: path style; AWS uses virtual hosts.
        s3={"addressing_style": "path" if endpoint_url else "virtual"},
    )
    return boto3.client("s3", endpoint_url=endpoint_url, region_name=region, config=config)


class S3ImageStorage:
    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.s3_bucket
        self._internal = _client(settings.s3_endpoint_url, settings.s3_region)
        # The phone may reach S3 by another host than the API (local only).
        self._public = _client(
            settings.s3_public_endpoint_url or settings.s3_endpoint_url, settings.s3_region
        )
        self._upload_ttl = settings.s3_upload_url_ttl_seconds
        self._download_ttl = settings.s3_download_url_ttl_seconds
        self._max_bytes = settings.s3_max_image_bytes

    def presign_upload(self, key: str) -> PresignedUpload:
        try:
            post = self._public.generate_presigned_post(
                Bucket=self._bucket,
                Key=key,
                Fields={"Content-Type": JPEG},
                Conditions=[
                    {"Content-Type": JPEG},
                    ["content-length-range", 1, self._max_bytes],
                ],
                ExpiresIn=self._upload_ttl,
            )
        except (BotoCoreError, ClientError) as error:
            raise self._unavailable(error) from error
        return PresignedUpload(
            url=post["url"],
            fields=dict(post["fields"]),
            expires_in=self._upload_ttl,
            max_bytes=self._max_bytes,
        )

    def presign_download(self, key: str) -> PresignedDownload:
        try:
            url = self._public.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=self._download_ttl,
            )
        except (BotoCoreError, ClientError) as error:
            raise self._unavailable(error) from error
        return PresignedDownload(url=url, expires_in=self._download_ttl)

    def stat_many(self, keys: list[str]) -> dict[str, StoredImage | None]:
        if not keys:
            return {}
        # In parallel: 20 sequential HeadObject calls would break p95 <= 500 ms (RNF16).
        with ThreadPoolExecutor(max_workers=min(_MAX_PARALLEL_HEADS, len(keys))) as pool:
            return dict(zip(keys, pool.map(self._stat, keys), strict=True))

    def _stat(self, key: str) -> StoredImage | None:
        try:
            head = self._internal.head_object(Bucket=self._bucket, Key=key)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise self._unavailable(error) from error
        except BotoCoreError as error:
            raise self._unavailable(error) from error
        return StoredImage(size=head["ContentLength"], content_type=head.get("ContentType"))

    @staticmethod
    def _unavailable(error: Exception) -> ServiceUnavailableError:
        logger.error("S3 error: %s", error)
        return ServiceUnavailableError(
            "No se pudo acceder al almacenamiento de imágenes. Intente de nuevo en unos minutos."
        )

"""Test doubles shared by the test modules."""

from bovi.clinical.domain.services.image_storage import (
    JPEG,
    PresignedDownload,
    PresignedUpload,
    StoredImage,
)


class FakeImageStorage:
    """In-memory S3: tests decide which photos are 'uploaded'."""

    def __init__(self, max_bytes: int = 512_000) -> None:
        self.objects: dict[str, StoredImage] = {}
        self.max_bytes = max_bytes
        self.head_calls = 0

    def put(self, key: str, size: int = 120_000, content_type: str | None = JPEG) -> None:
        self.objects[key] = StoredImage(size=size, content_type=content_type)

    def presign_upload(self, key: str) -> PresignedUpload:
        return PresignedUpload(
            url="http://s3.test/bovi-evaluaciones",
            fields={"key": key, "Content-Type": JPEG, "policy": "p", "x-amz-signature": "s"},
            expires_in=900,
            max_bytes=self.max_bytes,
        )

    def presign_download(self, key: str) -> PresignedDownload:
        return PresignedDownload(
            url=f"http://s3.test/bovi-evaluaciones/{key}?sig=s", expires_in=900
        )

    def stat_many(self, keys: list[str]) -> dict[str, StoredImage | None]:
        self.head_calls += len(keys)
        return {key: self.objects.get(key) for key in keys}

from dataclasses import dataclass
from typing import Protocol

JPEG = "image/jpeg"


@dataclass(frozen=True, slots=True)
class PresignedUpload:
    """POST form the app sends straight to S3: the photo never passes through the API."""

    url: str
    fields: dict[str, str]
    expires_in: int
    max_bytes: int


@dataclass(frozen=True, slots=True)
class PresignedDownload:
    url: str
    expires_in: int


@dataclass(frozen=True, slots=True)
class StoredImage:
    size: int
    content_type: str | None


class ImageStorage(Protocol):
    def presign_upload(self, key: str) -> PresignedUpload:
        """Only a JPEG of at most `max_bytes` is accepted by S3 (RNF18)."""
        ...

    def presign_download(self, key: str) -> PresignedDownload: ...

    def stat_many(self, keys: list[str]) -> dict[str, StoredImage | None]:
        """HeadObject of each key; None when the object does not exist."""
        ...

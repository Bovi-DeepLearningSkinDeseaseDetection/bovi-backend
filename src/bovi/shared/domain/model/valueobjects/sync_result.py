"""Outcome of each record of a sync batch (HU12, RNF10).

The app sends records with ids generated on the phone and may send the same
batch again after a network cut. Every record gets one of these answers, so
the app knows which ones to mark as synchronized.
"""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class SyncStatus(StrEnum):
    ACCEPTED = "accepted"
    """Saved now."""
    DUPLICATE = "duplicate"
    """Already saved before (same id): nothing changed."""
    MERGED = "merged"
    """Same record under another id (an animal with the same ear tag): use `canonical_id`."""
    REJECTED = "rejected"
    """Not saved: see `code` and `message`; the app may fix it and retry."""


@dataclass(frozen=True, slots=True)
class SyncItemResult:
    id: UUID
    status: SyncStatus
    canonical_id: UUID | None = None
    code: str | None = None
    message: str | None = None

    @property
    def is_synced(self) -> bool:
        return self.status is not SyncStatus.REJECTED

    @classmethod
    def accepted(cls, id: UUID) -> "SyncItemResult":
        return cls(id, SyncStatus.ACCEPTED, canonical_id=id)

    @classmethod
    def duplicate(cls, id: UUID) -> "SyncItemResult":
        return cls(id, SyncStatus.DUPLICATE, canonical_id=id)

    @classmethod
    def merged(cls, id: UUID, into: UUID) -> "SyncItemResult":
        return cls(id, SyncStatus.MERGED, canonical_id=into)

    @classmethod
    def rejected(cls, id: UUID, code: str, message: str) -> "SyncItemResult":
        return cls(id, SyncStatus.REJECTED, code=code, message=message)

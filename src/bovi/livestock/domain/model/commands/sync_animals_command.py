from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AnimalRecord:
    """An animal as the phone sends it, before validating it."""

    id: UUID
    ear_tag: str
    breed: str
    sex: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SyncAnimalsCommand:
    user_id: UUID
    animals: list[AnimalRecord]

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from bovi.livestock.domain.model.valueobjects.animal_sex import AnimalSex


class AnimalResource(BaseModel):
    """Same fields the app sends in /sync/animals, ready to save in Isar."""

    id: UUID
    ear_tag: str
    breed: str
    sex: AnimalSex
    created_at: datetime


class AnimalPageResource(BaseModel):
    items: list[AnimalResource]
    total: int = Field(description="Animales sincronizados del ganadero")
    next_cursor: str | None = Field(description="Envíelo como `cursor`; null en la última página")

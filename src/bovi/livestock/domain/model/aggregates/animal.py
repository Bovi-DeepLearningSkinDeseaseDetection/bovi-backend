from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from bovi.livestock.domain.model.valueobjects.animal_sex import AnimalSex
from bovi.livestock.domain.model.valueobjects.ear_tag import EarTag
from bovi.shared.domain.exceptions import ValidationError

BREED_MAX_LENGTH = 50


@dataclass(frozen=True, slots=True)
class Animal:
    """Animal of the farm of one farmer (HU15). Its id is generated on the phone."""

    id: UUID
    user_id: UUID
    ear_tag: EarTag
    breed: str
    sex: AnimalSex
    created_at: datetime

    @classmethod
    def from_device(
        cls,
        *,
        id: UUID,
        user_id: UUID,
        ear_tag: str,
        breed: str,
        sex: str,
        created_at: datetime,
    ) -> "Animal":
        clean_breed = " ".join(breed.split())
        if not clean_breed or len(clean_breed) > BREED_MAX_LENGTH:
            raise ValidationError(
                f"La raza debe tener entre 1 y {BREED_MAX_LENGTH} caracteres.",
                code="raza_invalida",
            )
        if created_at.tzinfo is None:
            raise ValidationError(
                "La fecha de registro debe incluir la zona horaria.", code="fecha_invalida"
            )
        return cls(
            id=id,
            user_id=user_id,
            ear_tag=EarTag(ear_tag),
            breed=clean_breed,
            sex=AnimalSex.parse(sex),
            created_at=created_at,
        )

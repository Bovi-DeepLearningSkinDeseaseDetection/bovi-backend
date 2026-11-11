from enum import StrEnum

from bovi.shared.domain.exceptions import ValidationError


class AnimalSex(StrEnum):
    """Same names as the enum of the app (AnimalSex.female / .male)."""

    FEMALE = "female"
    MALE = "male"

    @classmethod
    def parse(cls, value: str) -> "AnimalSex":
        try:
            return cls(value.strip().lower())
        except ValueError as error:
            raise ValidationError(
                "El sexo del animal debe ser female o male.", code="sexo_invalido"
            ) from error

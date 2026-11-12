from dataclasses import dataclass

from bovi.shared.domain.exceptions import ValidationError

MIN_LENGTH = 2
MAX_LENGTH = 100


@dataclass(frozen=True, slots=True)
class PersonName:
    """Name of the farmer, with inner spaces collapsed."""

    value: str

    def __post_init__(self) -> None:
        normalized = " ".join(self.value.split())
        if not MIN_LENGTH <= len(normalized) <= MAX_LENGTH:
            raise ValidationError(
                f"El nombre debe tener entre {MIN_LENGTH} y {MAX_LENGTH} caracteres.",
                code="nombre_invalido",
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

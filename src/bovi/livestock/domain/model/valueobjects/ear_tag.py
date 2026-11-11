import re
from dataclasses import dataclass

from bovi.shared.domain.exceptions import ValidationError

MAX_LENGTH = 20
_ALLOWED = re.compile(r"^[A-Z0-9-]+$")


@dataclass(frozen=True, slots=True)
class EarTag:
    """Ear tag number of an animal (HU15).

    Same rule as the app: stored without spaces and in upper case, so
    "pe 0012" and "PE0012" are the same tag.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = re.sub(r"\s+", "", self.value).upper()
        if not normalized:
            raise ValidationError("Ingrese el número de arete.", code="arete_invalido")
        if len(normalized) > MAX_LENGTH:
            raise ValidationError(
                f"El arete tiene como máximo {MAX_LENGTH} caracteres.", code="arete_invalido"
            )
        if not _ALLOWED.match(normalized):
            raise ValidationError("Use solo letras, números y guiones.", code="arete_invalido")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

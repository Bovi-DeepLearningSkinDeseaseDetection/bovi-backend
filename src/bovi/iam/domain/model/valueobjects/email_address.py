import re
from dataclasses import dataclass

from bovi.shared.domain.exceptions import ValidationError

_MAX_LENGTH = 254
# Pragmatic check: one @, no spaces, a dot in the domain. The real proof is the user using it.
_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class EmailAddress:
    """E-mail of the farmer; stored trimmed and in lower case, so it is unique ignoring case."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not normalized:
            raise ValidationError("Ingrese su correo electrónico.", code="correo_invalido")
        if len(normalized) > _MAX_LENGTH or not _PATTERN.match(normalized):
            raise ValidationError("El correo electrónico no es válido.", code="correo_invalido")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

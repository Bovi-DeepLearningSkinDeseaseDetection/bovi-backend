from dataclasses import dataclass

from bovi.shared.domain.exceptions import ValidationError

MIN_LENGTH = 8
# bcrypt only reads the first 72 bytes; longer passwords would be silently cut.
MAX_BYTES = 72


@dataclass(frozen=True, slots=True, repr=False)
class Password:
    """Plain password chosen on sign up. Never stored nor logged."""

    value: str

    def __post_init__(self) -> None:
        if len(self.value) < MIN_LENGTH:
            raise ValidationError(
                f"La contraseña debe tener al menos {MIN_LENGTH} caracteres.",
                code="contrasena_debil",
            )
        if len(self.value.encode("utf-8")) > MAX_BYTES:
            raise ValidationError("La contraseña es demasiado larga.", code="contrasena_debil")
        if not any(c.isalpha() for c in self.value) or not any(c.isdigit() for c in self.value):
            raise ValidationError(
                "La contraseña debe tener al menos una letra y un número.",
                code="contrasena_debil",
            )

    def __repr__(self) -> str:
        return "Password(***)"

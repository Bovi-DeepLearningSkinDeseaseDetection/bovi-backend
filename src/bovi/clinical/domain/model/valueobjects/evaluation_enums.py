"""Enums of an evaluation, with the same names as the enums of the app."""

from enum import StrEnum

from bovi.shared.domain.exceptions import ValidationError


class _Parsable(StrEnum):
    @classmethod
    def parse(cls, value: str, field: str):
        try:
            return cls(value)
        except ValueError as error:
            allowed = ", ".join(member.value for member in cls)
            raise ValidationError(
                f"El campo {field} debe ser uno de: {allowed}.", code="valor_invalido"
            ) from error


class BodyZone(_Parsable):
    HEAD = "head"
    NECK = "neck"
    BACK = "back"
    FLANK = "flank"
    LEGS = "legs"
    UDDER = "udder"
    OTHER = "other"


class ImageOrigin(_Parsable):
    CAMERA = "camera"
    GALLERY = "gallery"


class EvaluationOutcome(_Parsable):
    """Computed by the app with its confidence threshold; the backend never recomputes it."""

    HEALTHY = "healthy"
    LESION = "lesion"
    INCONCLUSIVE = "inconclusive"

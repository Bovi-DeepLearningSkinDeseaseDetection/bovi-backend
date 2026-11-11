"""Keyset pagination: stable pages even if new records arrive while restoring (HU13)."""

import base64
import binascii
import json
from dataclasses import dataclass
from typing import Any

from bovi.shared.domain.exceptions import ValidationError

DEFAULT_LIMIT = 50
MAX_LIMIT = 100


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T]
    total: int
    next_cursor: str | None
    """Opaque; send it back to get the next page. None on the last page."""


def check_limit(limit: int, maximum: int = MAX_LIMIT) -> int:
    if not 1 <= limit <= maximum:
        raise ValidationError(f"El límite debe estar entre 1 y {maximum}.", code="limite_invalido")
    return limit


def encode_cursor(values: dict[str, Any]) -> str:
    raw = json.dumps(values, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> dict[str, Any]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        values = json.loads(base64.urlsafe_b64decode(padded.encode()))
    except (ValueError, binascii.Error, UnicodeDecodeError) as error:
        raise invalid_cursor() from error
    if not isinstance(values, dict):
        raise invalid_cursor()
    return values


def invalid_cursor() -> ValidationError:
    return ValidationError(
        "El cursor de paginación no es válido. Vuelva a pedir la primera página.",
        code="cursor_invalido",
    )

from dataclasses import dataclass
from uuid import UUID

from bovi.shared.domain.model.valueobjects.page import DEFAULT_LIMIT


@dataclass(frozen=True, slots=True)
class GetAnimalsQuery:
    """Animals of the farmer, by ear tag, to restore them on a new phone (HU13)."""

    user_id: UUID
    limit: int = DEFAULT_LIMIT
    cursor: str | None = None

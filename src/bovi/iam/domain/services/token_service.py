from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass(frozen=True, slots=True, repr=False)
class TokenPair:
    access_token: str
    refresh_token: str
    access_expires_in: int
    refresh_expires_in: int


class TokenService(Protocol):
    def issue(self, user_id: UUID) -> TokenPair: ...

    def verify(self, token: str, expected: TokenType) -> UUID:
        """Returns the user id; raises InvalidTokenError if the token is not valid."""
        ...

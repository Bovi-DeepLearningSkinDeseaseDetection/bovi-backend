"""JWT (HS256) for the session of the farmer: access 1 h, refresh 30 days (RF12)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from bovi.iam.domain.exceptions.iam_errors import InvalidTokenError
from bovi.iam.domain.services.token_service import TokenPair, TokenType

_ALGORITHM = "HS256"


class JwtTokenService:
    def __init__(
        self,
        *,
        secret: str,
        issuer: str,
        access_ttl: timedelta,
        refresh_ttl: timedelta,
        # Only for issuing; PyJWT checks the expiry against the real time.
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._secret = secret
        self._issuer = issuer
        self._ttl = {TokenType.ACCESS: access_ttl, TokenType.REFRESH: refresh_ttl}
        self._clock = clock

    def issue(self, user_id: UUID) -> TokenPair:
        return TokenPair(
            access_token=self._encode(user_id, TokenType.ACCESS),
            refresh_token=self._encode(user_id, TokenType.REFRESH),
            access_expires_in=int(self._ttl[TokenType.ACCESS].total_seconds()),
            refresh_expires_in=int(self._ttl[TokenType.REFRESH].total_seconds()),
        )

    def verify(self, token: str, expected: TokenType) -> UUID:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[_ALGORITHM],
                issuer=self._issuer,
                options={"require": ["sub", "exp", "iat", "iss", "typ"]},
            )
            if claims["typ"] != expected:
                raise InvalidTokenError()
            return UUID(claims["sub"])
        except (jwt.InvalidTokenError, ValueError, KeyError) as error:
            raise InvalidTokenError() from error

    def _encode(self, user_id: UUID, kind: TokenType) -> str:
        now = self._clock()
        claims = {
            "sub": str(user_id),
            "typ": kind.value,
            "iss": self._issuer,
            "iat": int(now.timestamp()),
            "exp": int((now + self._ttl[kind]).timestamp()),
            "jti": uuid4().hex,
        }
        return jwt.encode(claims, self._secret, algorithm=_ALGORITHM)

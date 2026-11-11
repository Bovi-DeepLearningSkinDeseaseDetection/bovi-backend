from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from bovi.iam.domain.exceptions.iam_errors import InvalidTokenError
from bovi.iam.domain.services.token_service import TokenType
from bovi.iam.infrastructure.hashing.bcrypt.services.bcrypt_password_hasher import (
    BcryptPasswordHasher,
)
from bovi.iam.infrastructure.tokens.jwt.services.jwt_token_service import JwtTokenService

SECRET = "secreto-de-pruebas-con-mas-de-32-caracteres"


def _tokens(clock=lambda: datetime.now(UTC), secret: str = SECRET) -> JwtTokenService:
    return JwtTokenService(
        secret=secret,
        issuer="bovi-api",
        access_ttl=timedelta(hours=1),
        refresh_ttl=timedelta(days=30),
        clock=clock,
    )


def test_bcrypt_hash_is_not_the_password_and_verifies() -> None:
    hasher = BcryptPasswordHasher(rounds=4)

    hashed = hasher.hash("establo2026")

    assert hashed != "establo2026"
    assert hashed.startswith("$2b$04$")
    assert hasher.verify("establo2026", hashed)
    assert not hasher.verify("otra-clave1", hashed)


def test_bcrypt_rejects_a_corrupt_hash_instead_of_failing() -> None:
    assert not BcryptPasswordHasher(rounds=4).verify("establo2026", "no-es-un-hash")


def test_tokens_carry_the_user_and_their_lifetimes() -> None:
    user_id = uuid4()
    pair = _tokens().issue(user_id)

    assert pair.access_expires_in == 3600
    assert pair.refresh_expires_in == 30 * 24 * 3600
    assert _tokens().verify(pair.access_token, TokenType.ACCESS) == user_id
    assert _tokens().verify(pair.refresh_token, TokenType.REFRESH) == user_id


def test_access_token_is_not_accepted_as_refresh_token() -> None:
    pair = _tokens().issue(uuid4())

    with pytest.raises(InvalidTokenError):
        _tokens().verify(pair.access_token, TokenType.REFRESH)
    with pytest.raises(InvalidTokenError):
        _tokens().verify(pair.refresh_token, TokenType.ACCESS)


def test_expired_token_is_rejected() -> None:
    two_hours_ago = datetime.now(UTC) - timedelta(hours=2)
    pair = _tokens(clock=lambda: two_hours_ago).issue(uuid4())

    with pytest.raises(InvalidTokenError):
        _tokens().verify(pair.access_token, TokenType.ACCESS)


def test_token_signed_with_another_secret_is_rejected() -> None:
    pair = _tokens(secret="otro-secreto-de-mas-de-32-caracteres-x").issue(uuid4())

    with pytest.raises(InvalidTokenError):
        _tokens().verify(pair.access_token, TokenType.ACCESS)


def test_unsigned_token_is_rejected() -> None:
    forged = jwt.encode(
        {"sub": str(uuid4()), "typ": "access", "iss": "bovi-api", "iat": 0, "exp": 2**40},
        key=None,
        algorithm="none",
    )

    with pytest.raises(InvalidTokenError):
        _tokens().verify(forged, TokenType.ACCESS)


@pytest.mark.parametrize("garbage", ["", "abc", "a.b.c"])
def test_garbage_is_rejected(garbage: str) -> None:
    with pytest.raises(InvalidTokenError):
        _tokens().verify(garbage, TokenType.ACCESS)

"""Password hashing with bcrypt (RNF5).

Uses the `bcrypt` package directly: passlib is no longer maintained and breaks
with bcrypt 4.1 or newer.
"""

import contextlib

import bcrypt


class BcryptPasswordHasher:
    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds
        self._dummy_hash = bcrypt.hashpw(b"bovi-dummy-password-1", bcrypt.gensalt(rounds))

    def hash(self, plain: str) -> str:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(self._rounds)).decode("ascii")

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
        except ValueError:
            # Corrupt hash or a password over 72 bytes: never a match.
            return False

    def verify_dummy(self, plain: str) -> None:
        with contextlib.suppress(ValueError):
            bcrypt.checkpw(plain.encode("utf-8"), self._dummy_hash)

from typing import Protocol


class PasswordHasher(Protocol):
    def hash(self, plain: str) -> str: ...

    def verify(self, plain: str, hashed: str) -> bool: ...

    def verify_dummy(self, plain: str) -> None:
        """Spends the same time as verify(), for e-mails that do not exist."""
        ...

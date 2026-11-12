from typing import Protocol
from uuid import UUID

from bovi.iam.domain.model.aggregates.user import User
from bovi.iam.domain.model.valueobjects.email_address import EmailAddress


class UserRepository(Protocol):
    def add(self, user: User) -> None:
        """Raises EmailAlreadyRegisteredError if the e-mail is taken."""
        ...

    def find_by_id(self, user_id: UUID) -> User | None: ...

    def find_by_email(self, email: EmailAddress) -> User | None: ...

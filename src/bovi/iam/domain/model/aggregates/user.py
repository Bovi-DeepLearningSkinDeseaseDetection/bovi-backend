from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from bovi.iam.domain.exceptions.iam_errors import ConsentRequiredError, InactiveUserError
from bovi.iam.domain.model.valueobjects.email_address import EmailAddress
from bovi.iam.domain.model.valueobjects.person_name import PersonName


@dataclass(slots=True)
class User:
    """The farmer who owns the evaluations (HU14)."""

    id: UUID
    name: PersonName
    email: EmailAddress
    password_hash: str
    active: bool
    consent_accepted_at: datetime
    consent_version: str
    created_at: datetime

    @classmethod
    def register(
        cls,
        *,
        name: PersonName,
        email: EmailAddress,
        password_hash: str,
        consent_accepted: bool,
        consent_version: str,
        now: datetime,
    ) -> "User":
        # Ley N.° 29733: no personal data is kept without informed consent (RNF7).
        if not consent_accepted:
            raise ConsentRequiredError()
        return cls(
            id=uuid4(),
            name=name,
            email=email,
            password_hash=password_hash,
            active=True,
            consent_accepted_at=now,
            consent_version=consent_version,
            created_at=now,
        )

    def ensure_can_sign_in(self) -> None:
        if not self.active:
            raise InactiveUserError()

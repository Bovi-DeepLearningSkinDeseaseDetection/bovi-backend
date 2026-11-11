"""Use cases of the account of the farmer (HU14)."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from bovi.iam.domain.exceptions.iam_errors import InvalidCredentialsError, InvalidTokenError
from bovi.iam.domain.model.aggregates.user import User
from bovi.iam.domain.model.commands.auth_commands import (
    RefreshSessionCommand,
    SignInCommand,
    SignUpCommand,
)
from bovi.iam.domain.model.valueobjects.email_address import EmailAddress
from bovi.iam.domain.model.valueobjects.password import Password
from bovi.iam.domain.model.valueobjects.person_name import PersonName
from bovi.iam.domain.repositories.user_repository import UserRepository
from bovi.iam.domain.services.password_hasher import PasswordHasher
from bovi.iam.domain.services.token_service import TokenPair, TokenService, TokenType
from bovi.shared.domain.exceptions import ValidationError
from bovi.shared.domain.repositories.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    user: User
    tokens: TokenPair


class UserCommandService:
    def __init__(
        self,
        *,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        unit_of_work: UnitOfWork,
        consent_version: str,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        self._uow = unit_of_work
        self._consent_version = consent_version
        self._clock = clock

    def sign_up(self, command: SignUpCommand) -> AuthenticatedSession:
        """HU14, scenario 1: creates the account and opens the session at once."""
        name = PersonName(command.name)
        email = EmailAddress(command.email)
        password = Password(command.password)
        user = User.register(
            name=name,
            email=email,
            password_hash=self._hasher.hash(password.value),
            consent_accepted=command.consent_accepted,
            consent_version=self._consent_version,
            now=self._clock(),
        )
        self._users.add(user)
        self._uow.commit()
        return AuthenticatedSession(user, self._tokens.issue(user.id))

    def sign_in(self, command: SignInCommand) -> AuthenticatedSession:
        """HU14, scenarios 2 and 3."""
        try:
            email = EmailAddress(command.email)
        except ValidationError as error:
            raise InvalidCredentialsError() from error
        user = self._users.find_by_email(email)
        if user is None:
            # Same time as a real check, so response times do not reveal accounts.
            self._hasher.verify_dummy(command.password)
            raise InvalidCredentialsError()
        if not self._hasher.verify(command.password, user.password_hash):
            raise InvalidCredentialsError()
        user.ensure_can_sign_in()
        return AuthenticatedSession(user, self._tokens.issue(user.id))

    def refresh(self, command: RefreshSessionCommand) -> AuthenticatedSession:
        """Renews the access token with the refresh token (valid 30 days)."""
        user_id = self._tokens.verify(command.refresh_token, TokenType.REFRESH)
        user = self._users.find_by_id(user_id)
        if user is None:
            raise InvalidTokenError()
        user.ensure_can_sign_in()
        return AuthenticatedSession(user, self._tokens.issue(user.id))

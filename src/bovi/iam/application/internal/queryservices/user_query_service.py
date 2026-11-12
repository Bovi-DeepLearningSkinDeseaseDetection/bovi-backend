from bovi.iam.domain.exceptions.iam_errors import InvalidTokenError
from bovi.iam.domain.model.aggregates.user import User
from bovi.iam.domain.repositories.user_repository import UserRepository
from bovi.iam.domain.services.token_service import TokenService, TokenType


class UserQueryService:
    def __init__(self, *, users: UserRepository, tokens: TokenService) -> None:
        self._users = users
        self._tokens = tokens

    def authenticate(self, access_token: str) -> User:
        """User of a valid access token; the account must still exist and be active."""
        user_id = self._tokens.verify(access_token, TokenType.ACCESS)
        user = self._users.find_by_id(user_id)
        if user is None:
            raise InvalidTokenError()
        user.ensure_can_sign_in()
        return user

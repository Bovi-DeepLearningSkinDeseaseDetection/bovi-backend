"""Composition root of the iam context: builds its services for each request."""

from datetime import timedelta
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from bovi.iam.application.internal.commandservices.user_command_service import (
    UserCommandService,
)
from bovi.iam.application.internal.queryservices.user_query_service import UserQueryService
from bovi.iam.infrastructure.hashing.bcrypt.services.bcrypt_password_hasher import (
    BcryptPasswordHasher,
)
from bovi.iam.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_user_repository import (  # noqa: E501
    SqlAlchemyUserRepository,
)
from bovi.iam.infrastructure.tokens.jwt.services.jwt_token_service import JwtTokenService
from bovi.shared.infrastructure.configuration.settings import Settings, get_app_settings
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import get_session
from bovi.shared.infrastructure.persistence.sqlalchemy.repositories.sqlalchemy_unit_of_work import (  # noqa: E501
    SqlAlchemyUnitOfWork,
)


@lru_cache(maxsize=4)
def _hasher(rounds: int) -> BcryptPasswordHasher:
    return BcryptPasswordHasher(rounds)


def get_token_service(settings: Settings = Depends(get_app_settings)) -> JwtTokenService:
    return JwtTokenService(
        secret=settings.jwt_secret,
        issuer=settings.jwt_issuer,
        access_ttl=timedelta(minutes=settings.jwt_access_ttl_minutes),
        refresh_ttl=timedelta(days=settings.jwt_refresh_ttl_days),
    )


def get_user_command_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
    tokens: JwtTokenService = Depends(get_token_service),
) -> UserCommandService:
    return UserCommandService(
        users=SqlAlchemyUserRepository(session),
        hasher=_hasher(settings.bcrypt_rounds),
        tokens=tokens,
        unit_of_work=SqlAlchemyUnitOfWork(session),
        consent_version=settings.consent_version,
    )


def get_user_query_service(
    session: Session = Depends(get_session),
    tokens: JwtTokenService = Depends(get_token_service),
) -> UserQueryService:
    return UserQueryService(users=SqlAlchemyUserRepository(session), tokens=tokens)

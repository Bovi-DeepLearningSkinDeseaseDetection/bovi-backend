"""What the iam context offers to the other bounded contexts.

Usage in a controller of livestock or clinical:

    from bovi.iam.interfaces.acl.iam_context_facade import AuthenticatedUserId

    @router.get("/evaluations")
    def list_evaluations(user_id: AuthenticatedUserId): ...

The id always comes from the token, never from the request (aislamiento por usuario).
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from bovi.iam.application.internal.queryservices.user_query_service import UserQueryService
from bovi.iam.domain.exceptions.iam_errors import MissingTokenError
from bovi.iam.infrastructure.authorization.fastapi.configuration.bearer_scheme import (
    bearer_scheme,
)
from bovi.iam.interfaces.rest.dependencies import get_user_query_service


def get_authenticated_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    users: UserQueryService = Depends(get_user_query_service),
) -> UUID:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise MissingTokenError()
    return users.authenticate(credentials.credentials).id


AuthenticatedUserId = Annotated[UUID, Depends(get_authenticated_user_id)]

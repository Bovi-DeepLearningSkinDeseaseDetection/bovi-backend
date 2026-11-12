"""Endpoints /api/v1/auth: account and session of the farmer (HU14, RF12)."""

from fastapi import APIRouter, Depends, status

from bovi.iam.application.internal.commandservices.user_command_service import (
    UserCommandService,
)
from bovi.iam.interfaces.rest.dependencies import get_user_command_service
from bovi.iam.interfaces.rest.resources.auth_resources import (
    RefreshSessionResource,
    SessionResource,
    SignInResource,
    SignUpResource,
)
from bovi.iam.interfaces.rest.transform.auth_assemblers import (
    to_refresh_command,
    to_session_resource,
    to_sign_in_command,
    to_sign_up_command,
)
from bovi.shared.interfaces.rest.resources.error_resource import ErrorResource

router = APIRouter(prefix="/auth", tags=["IAM"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=SessionResource,
    summary="Crear la cuenta del ganadero",
    description="Requiere aceptar el consentimiento de datos. Devuelve la sesión iniciada.",
    responses={409: {"model": ErrorResource}, 422: {"model": ErrorResource}},
)
def register(
    resource: SignUpResource,
    service: UserCommandService = Depends(get_user_command_service),
) -> SessionResource:
    return to_session_resource(service.sign_up(to_sign_up_command(resource)))


@router.post(
    "/login",
    response_model=SessionResource,
    summary="Iniciar sesión",
    responses={401: {"model": ErrorResource}, 403: {"model": ErrorResource}},
)
def login(
    resource: SignInResource,
    service: UserCommandService = Depends(get_user_command_service),
) -> SessionResource:
    return to_session_resource(service.sign_in(to_sign_in_command(resource)))


@router.post(
    "/refresh",
    response_model=SessionResource,
    summary="Renovar el access token",
    description="Recibe el refresh token (30 días) y devuelve un par de tokens nuevo.",
    responses={401: {"model": ErrorResource}, 403: {"model": ErrorResource}},
)
def refresh(
    resource: RefreshSessionResource,
    service: UserCommandService = Depends(get_user_command_service),
) -> SessionResource:
    return to_session_resource(service.refresh(to_refresh_command(resource)))

from bovi.iam.application.internal.commandservices.user_command_service import (
    AuthenticatedSession,
)
from bovi.iam.domain.model.commands.auth_commands import (
    RefreshSessionCommand,
    SignInCommand,
    SignUpCommand,
)
from bovi.iam.interfaces.rest.resources.auth_resources import (
    RefreshSessionResource,
    SessionResource,
    SignInResource,
    SignUpResource,
    UserResource,
)


def to_sign_up_command(resource: SignUpResource) -> SignUpCommand:
    return SignUpCommand(
        name=resource.name,
        email=resource.email,
        password=resource.password,
        consent_accepted=resource.consent_accepted,
    )


def to_sign_in_command(resource: SignInResource) -> SignInCommand:
    return SignInCommand(email=resource.email, password=resource.password)


def to_refresh_command(resource: RefreshSessionResource) -> RefreshSessionCommand:
    return RefreshSessionCommand(refresh_token=resource.refresh_token)


def to_session_resource(session: AuthenticatedSession) -> SessionResource:
    user = session.user
    return SessionResource(
        access_token=session.tokens.access_token,
        refresh_token=session.tokens.refresh_token,
        expires_in=session.tokens.access_expires_in,
        refresh_expires_in=session.tokens.refresh_expires_in,
        user=UserResource(id=user.id, name=user.name.value, email=user.email.value),
    )

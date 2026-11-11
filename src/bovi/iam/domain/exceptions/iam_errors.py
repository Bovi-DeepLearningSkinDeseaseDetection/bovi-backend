"""Errors of the iam context, with the messages the farmer reads in the app."""

from bovi.shared.domain.exceptions import (
    AuthenticationError,
    ConflictError,
    PermissionDeniedError,
    ValidationError,
)


class ConsentRequiredError(ValidationError):
    def __init__(self) -> None:
        super().__init__(
            "Debe aceptar el consentimiento de tratamiento de datos para crear su cuenta.",
            code="consentimiento_requerido",
        )


class EmailAlreadyRegisteredError(ConflictError):
    def __init__(self) -> None:
        super().__init__(
            "Ya existe una cuenta con este correo. Inicie sesión.", code="correo_registrado"
        )


class InvalidCredentialsError(AuthenticationError):
    """Same message for unknown e-mail and wrong password (HU14, scenario 3)."""

    def __init__(self) -> None:
        super().__init__("Correo o contraseña incorrectos", code="credenciales_invalidas")


class InvalidTokenError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__(
            "Su sesión no es válida o expiró. Inicie sesión de nuevo.", code="token_invalido"
        )


class MissingTokenError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Necesita iniciar sesión para continuar.", code="no_autenticado")


class InactiveUserError(PermissionDeniedError):
    def __init__(self) -> None:
        super().__init__("Su cuenta está desactivada.", code="cuenta_desactivada")

"""Base errors of the domain.

Each bounded context raises subclasses of these errors with a message in
Spanish, written for the farmer who reads it in the app. The REST layer maps
each kind to its HTTP status, so the domain never knows about HTTP.
"""


class DomainError(Exception):
    """A business rule was broken."""

    code = "regla_de_negocio"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class ValidationError(DomainError):
    """The data does not meet the rules of the domain."""

    code = "datos_invalidos"


class NotFoundError(DomainError):
    """The resource does not exist or does not belong to the user."""

    code = "no_encontrado"


class ConflictError(DomainError):
    """The resource already exists or clashes with another one."""

    code = "conflicto"


class AuthenticationError(DomainError):
    """The credentials or the token are not valid."""

    code = "no_autenticado"


class PermissionDeniedError(DomainError):
    """The user is authenticated but cannot do this."""

    code = "sin_permiso"


class ServiceUnavailableError(DomainError):
    """A service the use case needs (S3, for example) does not answer; retry later."""

    code = "servicio_no_disponible"

"""Turns every error into an ErrorResource with a message in Spanish."""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from bovi.shared.domain.exceptions import (
    AuthenticationError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    ServiceUnavailableError,
    ValidationError,
)
from bovi.shared.interfaces.rest.resources.error_resource import ErrorResource, FieldErrorResource

logger = logging.getLogger(__name__)

_DOMAIN_STATUS: list[tuple[type[DomainError], int]] = [
    (ValidationError, status.HTTP_422_UNPROCESSABLE_CONTENT),
    (NotFoundError, status.HTTP_404_NOT_FOUND),
    (ConflictError, status.HTTP_409_CONFLICT),
    (AuthenticationError, status.HTTP_401_UNAUTHORIZED),
    (PermissionDeniedError, status.HTTP_403_FORBIDDEN),
    (ServiceUnavailableError, status.HTTP_503_SERVICE_UNAVAILABLE),
]

_HTTP_MESSAGES: dict[int, tuple[str, str]] = {
    400: ("solicitud_invalida", "La solicitud no es válida."),
    401: ("no_autenticado", "Necesita iniciar sesión para continuar."),
    403: ("sin_permiso", "No tiene permiso para realizar esta acción."),
    404: ("no_encontrado", "El recurso solicitado no existe."),
    405: ("metodo_no_permitido", "La operación no está permitida en esta ruta."),
    413: ("contenido_muy_grande", "El contenido enviado es demasiado grande."),
    415: ("tipo_no_soportado", "El tipo de contenido no está soportado."),
    429: (
        "demasiadas_solicitudes",
        "Demasiadas solicitudes. Espere un momento e intente de nuevo.",
    ),
}

_INTERNAL_ERROR = ErrorResource(
    code="error_interno",
    message="Ocurrió un error inesperado. Intente de nuevo más tarde.",
)

_LOCATIONS = {"body", "query", "path", "header", "cookie"}


def _count(amount: Any, singular: str, plural: str) -> str:
    return f"{amount} {singular if amount == 1 else plural}"


def _field_message(error: dict[str, Any]) -> str:
    """Spanish message for one Pydantic error."""
    ctx = error.get("ctx") or {}
    kind = error.get("type", "")
    match kind:
        case "missing":
            return "Este campo es obligatorio."
        case "string_too_short":
            return f"Debe tener al menos {_count(ctx.get('min_length'), 'carácter', 'caracteres')}."
        case "string_too_long":
            return (
                f"Debe tener como máximo {_count(ctx.get('max_length'), 'carácter', 'caracteres')}."
            )
        case "too_short":
            return f"Debe tener al menos {_count(ctx.get('min_length'), 'elemento', 'elementos')}."
        case "too_long":
            return (
                f"Debe tener como máximo {_count(ctx.get('max_length'), 'elemento', 'elementos')}."
            )
        case "string_type":
            return "Debe ser un texto."
        case "string_pattern_mismatch":
            return "El formato no es válido."
        case "int_type" | "int_parsing" | "int_from_float":
            return "Debe ser un número entero."
        case "float_type" | "float_parsing":
            return "Debe ser un número."
        case "bool_type" | "bool_parsing":
            return "Debe ser verdadero o falso."
        case "greater_than":
            return f"Debe ser mayor que {ctx.get('gt')}."
        case "greater_than_equal":
            return f"Debe ser mayor o igual que {ctx.get('ge')}."
        case "less_than":
            return f"Debe ser menor que {ctx.get('lt')}."
        case "less_than_equal":
            return f"Debe ser menor o igual que {ctx.get('le')}."
        case "uuid_type" | "uuid_parsing" | "uuid_version":
            return "Debe ser un UUID válido."
        case "datetime_type" | "datetime_parsing" | "datetime_from_date_parsing":
            return "Debe ser una fecha y hora válida (ISO 8601)."
        case "timezone_aware":
            return "La fecha y hora debe incluir la zona horaria."
        case "enum" | "literal_error":
            return f"Debe ser uno de estos valores: {ctx.get('expected')}."
        case "list_type":
            return "Debe ser una lista."
        case "dict_type" | "model_type" | "model_attributes_type":
            return "Debe ser un objeto."
        case "extra_forbidden":
            return "Este campo no está permitido."
        case "json_invalid":
            return "El cuerpo de la solicitud no es un JSON válido."
        case "value_error" | "assertion_error":
            # Our own validators already write their message in Spanish.
            error_obj = ctx.get("error")
            return str(error_obj) if error_obj else "El valor no es válido."
        case _:
            return "El valor no es válido."


def _field_path(loc: tuple[Any, ...] | list[Any]) -> str:
    parts = list(loc)
    if parts and parts[0] in _LOCATIONS:
        parts = parts[1:]
    path = ""
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}" if path else str(part)
    return path or "body"


def _json(resource: ErrorResource, status_code: int, headers: dict[str, str] | None = None):
    return JSONResponse(resource.model_dump(), status_code=status_code, headers=headers)


async def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
    status_code = next(
        (code for kind, code in _DOMAIN_STATUS if isinstance(exc, kind)),
        status.HTTP_400_BAD_REQUEST,
    )
    headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
    return _json(ErrorResource(code=exc.code, message=exc.message), status_code, headers)


async def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        FieldErrorResource(field=_field_path(error.get("loc", ())), message=_field_message(error))
        for error in exc.errors()
    ]
    resource = ErrorResource(
        code="datos_invalidos",
        message="Algunos datos enviados no son válidos.",
        details=details,
    )
    return _json(resource, status.HTTP_422_UNPROCESSABLE_CONTENT)


async def _handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code, message = _HTTP_MESSAGES.get(
        exc.status_code, ("error_http", "La solicitud no se pudo completar.")
    )
    # The detail of framework errors is in English ("There was an error parsing the body"),
    # so it is never shown. Business errors are DomainError, which carry their own message.
    return _json(ErrorResource(code=code, message=message), exc.status_code, exc.headers)


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return _json(_INTERNAL_ERROR, status.HTTP_500_INTERNAL_SERVER_ERROR)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _handle_domain_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)

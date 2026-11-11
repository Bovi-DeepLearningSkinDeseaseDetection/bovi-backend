"""Metadata of the OpenAPI documentation (/docs and /redoc)."""

from typing import Any

from bovi.shared.infrastructure.configuration.settings import Settings

TITLE = "Bovi API"

DESCRIPTION = """
Backend de **Bovi**, la app que detecta de forma preliminar enfermedades cutáneas
del ganado bovino. La detección ocurre en el celular; este servicio solo:

1. registra e inicia sesión al ganadero (JWT),
2. recibe la sincronización de animales y evaluaciones,
3. entrega URLs prefirmadas de S3 para subir y descargar las imágenes,
4. devuelve el historial para restaurarlo en un dispositivo nuevo.

Todas las rutas, salvo `/health` y `/api/v1/auth/*`, requieren un token JWT.
Los mensajes de error están en español.
"""

TAGS: list[dict[str, str]] = [
    {"name": "Salud", "description": "Estado del servicio."},
    {"name": "IAM", "description": "Registro, inicio de sesión y renovación del token."},
    {"name": "Livestock", "description": "Animales del establo."},
    {"name": "Clinical", "description": "Evaluaciones, imágenes e historial."},
]


def openapi_options(settings: Settings) -> dict[str, Any]:
    """Keyword arguments for FastAPI() that configure the documentation."""
    enabled = settings.docs_enabled
    return {
        "title": TITLE,
        "description": DESCRIPTION,
        "openapi_tags": TAGS,
        "docs_url": "/docs" if enabled else None,
        "redoc_url": "/redoc" if enabled else None,
        "openapi_url": "/openapi.json" if enabled else None,
    }

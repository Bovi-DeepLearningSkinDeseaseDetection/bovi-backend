"""Endpoints /api/v1/media: presigned URLs of the photos (RNF18)."""

from fastapi import APIRouter, Depends

from bovi.clinical.application.internal.commandservices.media_command_service import (
    MediaCommandService,
)
from bovi.clinical.interfaces.rest.dependencies import get_media_command_service
from bovi.clinical.interfaces.rest.resources.clinical_resources import (
    DownloadUrlsResource,
    ImageUrlsRequestResource,
    UploadUrlsResource,
)
from bovi.clinical.interfaces.rest.transform.clinical_assemblers import (
    to_download_urls_resource,
    to_image_urls_command,
    to_upload_urls_resource,
)
from bovi.iam.interfaces.acl.iam_context_facade import AuthenticatedUserId
from bovi.shared.interfaces.rest.resources.error_resource import ErrorResource

router = APIRouter(prefix="/media", tags=["Clinical"])
_ERRORS = {
    401: {"model": ErrorResource},
    422: {"model": ErrorResource},
    503: {"model": ErrorResource},
}


@router.post(
    "/upload-url",
    response_model=UploadUrlsResource,
    summary="URLs prefirmadas para subir fotos a S3",
    description=(
        "Una URL por evaluación (hasta 20). La app envía la foto directo a S3 con un POST "
        "multipart: primero los `fields` y al final el archivo en el campo `file`. S3 solo acepta "
        "un JPEG de hasta `max_bytes`. La URL vence en 15 minutos. Si la evaluación ya está "
        "sincronizada responde `already_synced` y no entrega URL."
    ),
    responses=_ERRORS,
)
def upload_urls(
    resource: ImageUrlsRequestResource,
    user_id: AuthenticatedUserId,
    service: MediaCommandService = Depends(get_media_command_service),
) -> UploadUrlsResource:
    return to_upload_urls_resource(service.upload_urls(to_image_urls_command(user_id, resource)))


@router.post(
    "/download-url",
    response_model=DownloadUrlsResource,
    summary="URLs prefirmadas para descargar fotos de S3",
    description=(
        "Para restaurar el historial (HU13). Solo entrega fotos de evaluaciones sincronizadas del "
        "propio ganadero; cualquier otro id responde `not_found`."
    ),
    responses=_ERRORS,
)
def download_urls(
    resource: ImageUrlsRequestResource,
    user_id: AuthenticatedUserId,
    service: MediaCommandService = Depends(get_media_command_service),
) -> DownloadUrlsResource:
    return to_download_urls_resource(
        service.download_urls(to_image_urls_command(user_id, resource))
    )

from uuid import UUID

from bovi.clinical.application.internal.commandservices.media_command_service import (
    DownloadUrl,
    UploadUrl,
)
from bovi.clinical.domain.model.commands.clinical_commands import (
    ClinicalCodeRecord,
    EvaluationRecord,
    ProbabilityRecord,
    RequestImageUrlsCommand,
    SyncEvaluationsCommand,
)
from bovi.clinical.interfaces.rest.resources.clinical_resources import (
    DownloadUrlResource,
    DownloadUrlsResource,
    EvaluationSyncBatchResource,
    ImageUrlsRequestResource,
    PresignedUploadResource,
    UploadUrlResource,
    UploadUrlsResource,
)


def to_sync_evaluations_command(
    user_id: UUID, resource: EvaluationSyncBatchResource
) -> SyncEvaluationsCommand:
    return SyncEvaluationsCommand(
        user_id=user_id,
        evaluations=[
            EvaluationRecord(
                id=e.id,
                evaluated_at=e.evaluated_at,
                image_origin=e.image_origin,
                probabilities=[ProbabilityRecord(p.label, p.probability) for p in e.probabilities],
                predicted_class=e.predicted_class,
                confidence=e.confidence,
                outcome=e.outcome,
                clinical_codes=[
                    ClinicalCodeRecord(c.system, c.code, c.display) for c in e.clinical_codes
                ],
                catalog_version=e.catalog_version,
                model_version=e.model_version,
                inference_ms=e.inference_ms,
                animal_id=e.animal_id,
                body_zone=e.body_zone,
            )
            for e in resource.evaluations
        ],
    )


def to_image_urls_command(
    user_id: UUID, resource: ImageUrlsRequestResource
) -> RequestImageUrlsCommand:
    return RequestImageUrlsCommand(user_id=user_id, evaluation_ids=resource.evaluation_ids)


def to_upload_urls_resource(items: list[UploadUrl]) -> UploadUrlsResource:
    return UploadUrlsResource(
        items=[
            UploadUrlResource(
                evaluation_id=i.evaluation_id,
                status=i.status,
                image_key=i.image_key,
                upload=(
                    PresignedUploadResource(
                        url=i.upload.url,
                        fields=i.upload.fields,
                        expires_in=i.upload.expires_in,
                        max_bytes=i.upload.max_bytes,
                    )
                    if i.upload
                    else None
                ),
            )
            for i in items
        ]
    )


def to_download_urls_resource(items: list[DownloadUrl]) -> DownloadUrlsResource:
    return DownloadUrlsResource(
        items=[
            DownloadUrlResource(
                evaluation_id=i.evaluation_id,
                status=i.status,
                url=i.download.url if i.download else None,
                expires_in=i.download.expires_in if i.download else None,
            )
            for i in items
        ]
    )

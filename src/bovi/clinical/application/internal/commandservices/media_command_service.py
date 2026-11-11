"""Presigned URLs so the app uploads and downloads photos straight to S3 (RNF18)."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from bovi.clinical.domain.model.commands.clinical_commands import RequestImageUrlsCommand
from bovi.clinical.domain.model.valueobjects.image_key import image_key_for
from bovi.clinical.domain.repositories.evaluation_repository import EvaluationRepository
from bovi.clinical.domain.services.image_storage import (
    ImageStorage,
    PresignedDownload,
    PresignedUpload,
)
from bovi.shared.domain.exceptions.sync_errors import check_batch_size


class UrlStatus(StrEnum):
    READY = "ready"
    """The URL is in the answer."""
    ALREADY_SYNCED = "already_synced"
    """Upload only: the evaluation is already saved with its photo; mark it as synced."""
    NOT_FOUND = "not_found"
    """Download only: the farmer has no synced evaluation with this id."""
    REJECTED = "rejected"
    """The id belongs to another record: generate a new one."""


@dataclass(frozen=True, slots=True)
class UploadUrl:
    evaluation_id: UUID
    status: UrlStatus
    image_key: str | None = None
    upload: PresignedUpload | None = None


@dataclass(frozen=True, slots=True)
class DownloadUrl:
    evaluation_id: UUID
    status: UrlStatus
    download: PresignedDownload | None = None


class MediaCommandService:
    def __init__(
        self, *, evaluations: EvaluationRepository, storage: ImageStorage, max_batch: int
    ) -> None:
        self._evaluations = evaluations
        self._storage = storage
        self._max_batch = max_batch

    def upload_urls(self, command: RequestImageUrlsCommand) -> list[UploadUrl]:
        """One presigned POST per evaluation still to sync (valid 15 minutes)."""
        ids = list(dict.fromkeys(command.evaluation_ids))
        check_batch_size(len(ids), self._max_batch, "evaluaciones")
        owners = self._evaluations.owners_of(ids)
        answers = []
        for evaluation_id in ids:
            owner = owners.get(evaluation_id)
            if owner == command.user_id:
                # Saved and immutable: its photo must not be replaced.
                answers.append(UploadUrl(evaluation_id, UrlStatus.ALREADY_SYNCED))
            elif owner is not None:
                answers.append(UploadUrl(evaluation_id, UrlStatus.REJECTED))
            else:
                key = image_key_for(command.user_id, evaluation_id)
                answers.append(
                    UploadUrl(
                        evaluation_id, UrlStatus.READY, key, self._storage.presign_upload(key)
                    )
                )
        return answers

    def download_urls(self, command: RequestImageUrlsCommand) -> list[DownloadUrl]:
        """Presigned GET of the photos of the farmer's own synced evaluations (HU13)."""
        ids = list(dict.fromkeys(command.evaluation_ids))
        check_batch_size(len(ids), self._max_batch, "evaluaciones")
        owners = self._evaluations.owners_of(ids)
        return [
            DownloadUrl(
                evaluation_id,
                UrlStatus.READY,
                self._storage.presign_download(image_key_for(command.user_id, evaluation_id)),
            )
            if owners.get(evaluation_id) == command.user_id
            # Another farmer's id looks exactly like a missing one: nothing leaks.
            else DownloadUrl(evaluation_id, UrlStatus.NOT_FOUND)
            for evaluation_id in ids
        ]

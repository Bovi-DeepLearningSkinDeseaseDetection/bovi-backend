from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from bovi.clinical.application.internal.commandservices.media_command_service import UrlStatus

_EVALUATION_EXAMPLE = {
    "id": "6f1c2a7e-9d4b-4c1a-8f00-000000000001",
    "evaluated_at": "2026-11-11T16:47:00-05:00",
    "image_origin": "camera",
    "probabilities": [
        {"label": "sarna", "probability": 0.8193},
        {"label": "dermatofitosis", "probability": 0.1507},
        {"label": "papilomatosis", "probability": 0.0257},
        {"label": "piel_sana", "probability": 0.0028},
        {"label": "miasis", "probability": 0.0015},
    ],
    "predicted_class": "sarna",
    "confidence": 0.8193,
    "outcome": "lesion",
    "clinical_codes": [
        {"system": "http://id.nlm.nih.gov/mesh", "code": "D008924", "display": "Mite Infestations"},
        {"system": "http://id.nlm.nih.gov/mesh", "code": "D002418", "display": "Cattle Diseases"},
        {
            "system": "http://purl.obolibrary.org/obo/NCBITaxon",
            "code": "420257",
            "display": "Chorioptes bovis",
        },
    ],
    "catalog_version": "2026.1",
    "model_version": "v7c_peso_pap",
    "inference_ms": 180,
    "animal_id": "0f8b7c1e-2a52-4c4f-9a43-6f1d2b9c1a01",
    "body_zone": "flank",
}


class ProbabilityResource(BaseModel):
    label: str = Field(max_length=30)
    probability: float


class ClinicalCodeResource(BaseModel):
    system: str = Field(max_length=100)
    code: str = Field(max_length=40)
    display: str = Field(max_length=200)


class EvaluationSyncItemResource(BaseModel):
    """Evaluation as stored on the phone (Evaluation of the app)."""

    id: UUID = Field(description="uuid de la evaluación; también es la clave de idempotencia")
    evaluated_at: datetime = Field(description="Fecha y hora del análisis, con zona horaria")
    image_origin: str = Field(max_length=20, description="camera | gallery")
    probabilities: list[ProbabilityResource] = Field(max_length=20)
    predicted_class: str = Field(max_length=30)
    confidence: float
    outcome: str = Field(max_length=20, description="healthy | lesion | inconclusive")
    clinical_codes: list[ClinicalCodeResource] = Field(default_factory=list, max_length=20)
    catalog_version: str | None = Field(default=None, max_length=40)
    model_version: str = Field(max_length=80)
    inference_ms: int | None = None
    animal_id: UUID | None = Field(default=None, description="uuid del animal ya sincronizado")
    body_zone: str | None = Field(
        default=None, max_length=20, description="head | neck | back | flank | legs | udder | other"
    )


class EvaluationSyncBatchResource(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"evaluations": [_EVALUATION_EXAMPLE]}})

    evaluations: list[EvaluationSyncItemResource]


class ImageUrlsRequestResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"evaluation_ids": [_EVALUATION_EXAMPLE["id"]]}}
    )

    evaluation_ids: list[UUID]


class PresignedUploadResource(BaseModel):
    url: str = Field(description="URL a la que la app envía un POST multipart/form-data")
    fields: dict[str, str] = Field(
        description="Campos del formulario, en este orden y antes del campo `file`"
    )
    expires_in: int = Field(description="Segundos de validez")
    max_bytes: int = Field(description="Tamaño máximo de la foto")


class UploadUrlResource(BaseModel):
    evaluation_id: UUID
    status: UrlStatus
    image_key: str | None = None
    upload: PresignedUploadResource | None = None


class UploadUrlsResource(BaseModel):
    items: list[UploadUrlResource]


class DownloadUrlResource(BaseModel):
    evaluation_id: UUID
    status: UrlStatus
    url: str | None = None
    expires_in: int | None = None


class DownloadUrlsResource(BaseModel):
    items: list[DownloadUrlResource]

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProbabilityRecord:
    label: str
    probability: float


@dataclass(frozen=True, slots=True)
class ClinicalCodeRecord:
    system: str
    code: str
    display: str


@dataclass(frozen=True, slots=True)
class EvaluationRecord:
    """An evaluation as the phone sends it, before validating it."""

    id: UUID
    evaluated_at: datetime
    image_origin: str
    probabilities: list[ProbabilityRecord]
    predicted_class: str
    confidence: float
    outcome: str
    clinical_codes: list[ClinicalCodeRecord]
    catalog_version: str | None
    model_version: str
    inference_ms: int | None
    animal_id: UUID | None
    body_zone: str | None


@dataclass(frozen=True, slots=True)
class SyncEvaluationsCommand:
    user_id: UUID
    evaluations: list[EvaluationRecord]


@dataclass(frozen=True, slots=True)
class RequestImageUrlsCommand:
    user_id: UUID
    evaluation_ids: list[UUID]

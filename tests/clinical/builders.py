"""Evaluations as the app sends them, built from real outputs of the v7c model."""

from typing import Any
from uuid import UUID, uuid4

MESH = "http://id.nlm.nih.gov/mesh"
NCBI = "http://purl.obolibrary.org/obo/NCBITaxon"

# Probabilities of real photos (test/fixtures/paridad of the app).
SARNA = [
    {"label": "dermatofitosis", "probability": 0.006108},
    {"label": "miasis", "probability": 0.000231},
    {"label": "papilomatosis", "probability": 0.015779},
    {"label": "piel_sana", "probability": 0.002489},
    {"label": "sarna", "probability": 0.975393},
]
SANA = [
    {"label": "dermatofitosis", "probability": 0.00045},
    {"label": "miasis", "probability": 0.0},
    {"label": "papilomatosis", "probability": 2e-06},
    {"label": "piel_sana", "probability": 0.999538},
    {"label": "sarna", "probability": 1e-05},
]
NO_CONCLUYENTE = [
    {"label": "dermatofitosis", "probability": 0.465752},
    {"label": "miasis", "probability": 4.7e-05},
    {"label": "papilomatosis", "probability": 0.452374},
    {"label": "piel_sana", "probability": 0.016969},
    {"label": "sarna", "probability": 0.064857},
]
SARNA_CODES = [
    {"system": MESH, "code": "D008924", "display": "Mite Infestations"},
    {"system": MESH, "code": "D002418", "display": "Cattle Diseases"},
    {"system": NCBI, "code": "420257", "display": "Chorioptes bovis"},
]


def evaluation(
    *, id: UUID | None = None, animal_id: UUID | None = None, **overrides: Any
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "id": str(id or uuid4()),
        "evaluated_at": "2026-11-11T16:47:00-05:00",
        "image_origin": "camera",
        "probabilities": SARNA,
        "predicted_class": "sarna",
        "confidence": 0.975393,
        "outcome": "lesion",
        "clinical_codes": SARNA_CODES,
        "catalog_version": "2026.1",
        "model_version": "v7c_peso_pap",
        "inference_ms": 180,
        "animal_id": str(animal_id) if animal_id else None,
        "body_zone": "flank" if animal_id else None,
    }
    body.update(overrides)
    return body


def healthy(**overrides: Any) -> dict[str, Any]:
    return evaluation(
        probabilities=SANA,
        predicted_class="piel_sana",
        confidence=0.999538,
        outcome="healthy",
        clinical_codes=[],
        **overrides,
    )


def inconclusive(**overrides: Any) -> dict[str, Any]:
    return evaluation(
        probabilities=NO_CONCLUYENTE,
        predicted_class="dermatofitosis",
        confidence=0.465752,
        outcome="inconclusive",
        clinical_codes=[],
        **overrides,
    )


def animal(**overrides: Any) -> dict[str, Any]:
    body = {
        "id": str(uuid4()),
        "ear_tag": "PE-0012",
        "breed": "Holstein",
        "sex": "female",
        "created_at": "2026-11-10T09:30:00-05:00",
    }
    body.update(overrides)
    return body

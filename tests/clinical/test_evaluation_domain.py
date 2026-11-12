from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from bovi.clinical.domain.model.aggregates.evaluation import Evaluation
from bovi.clinical.domain.model.valueobjects.class_probabilities import (
    ClassProbabilities,
    ClassProbability,
)
from bovi.clinical.domain.model.valueobjects.clinical_code import ClinicalCode
from bovi.clinical.domain.model.valueobjects.evaluation_enums import (
    BodyZone,
    EvaluationOutcome,
    ImageOrigin,
)
from bovi.shared.domain.exceptions import ValidationError
from tests.clinical.builders import MESH, NO_CONCLUYENTE, SANA, SARNA

NOW = datetime(2026, 11, 11, 22, 0, tzinfo=UTC)
USER = UUID("11111111-1111-1111-1111-111111111111")


def _probs(items: list[dict]) -> ClassProbabilities:
    return ClassProbabilities(tuple(ClassProbability(i["label"], i["probability"]) for i in items))


def _record(**overrides) -> Evaluation:
    values = {
        "id": uuid4(),
        "user_id": USER,
        "evaluated_at": NOW - timedelta(hours=1),
        "image_origin": ImageOrigin.CAMERA,
        "probabilities": _probs(SARNA),
        "predicted_class": "sarna",
        "confidence": 0.975393,
        "outcome": EvaluationOutcome.LESION,
        "clinical_codes": (ClinicalCode(MESH, "D008924", "Mite Infestations"),),
        "catalog_version": "2026.1",
        "model_version": "v7c",
        "inference_ms": 180,
        "animal_id": None,
        "body_zone": BodyZone.FLANK,
        "now": NOW,
    }
    values.update(overrides)
    return Evaluation.record(**values)


def test_a_lesion_keeps_everything_for_traceability() -> None:
    evaluation = _record()

    assert evaluation.model_version == "v7c"
    assert len(evaluation.probabilities.items) == 5
    assert evaluation.image_key == f"evaluaciones/{USER}/{evaluation.id}.jpg"


def test_healthy_and_inconclusive_results_are_valid() -> None:
    _record(
        probabilities=_probs(SANA),
        predicted_class="piel_sana",
        confidence=0.999538,
        outcome=EvaluationOutcome.HEALTHY,
        clinical_codes=(),
    )
    _record(
        probabilities=_probs(NO_CONCLUYENTE),
        predicted_class="dermatofitosis",
        confidence=0.465752,
        outcome=EvaluationOutcome.INCONCLUSIVE,
        clinical_codes=(),
    )


def test_old_models_with_two_classes_are_accepted() -> None:
    _record(
        probabilities=_probs(
            [
                {"label": "dermatofitosis", "probability": 0.91},
                {"label": "sana", "probability": 0.09},
            ]
        ),
        predicted_class="dermatofitosis",
        confidence=0.91,
    )


@pytest.mark.parametrize(
    ("items", "message"),
    [
        ([{"label": "sarna", "probability": 1.0}], "cada clase"),
        (
            [{"label": "sarna", "probability": 0.5}, {"label": "sarna", "probability": 0.5}],
            "repetidas",
        ),
        (
            [{"label": "sarna", "probability": 0.5}, {"label": "tiña", "probability": 0.5}],
            "desconocida",
        ),
        (
            [{"label": "sarna", "probability": 1.2}, {"label": "miasis", "probability": -0.2}],
            "entre 0 y 1",
        ),
        (
            [{"label": "sarna", "probability": 0.7}, {"label": "miasis", "probability": 0.2}],
            "sumar 1",
        ),
    ],
)
def test_invalid_probabilities(items: list[dict], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        _probs(items)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"predicted_class": "miasis"}, "mayor probabilidad"),
        ({"confidence": 0.81}, "confianza no coincide"),
        ({"outcome": EvaluationOutcome.HEALTHY}, "saludable"),
        ({"outcome": EvaluationOutcome.INCONCLUSIVE}, "Solo un resultado con lesión"),
        ({"evaluated_at": datetime(2026, 11, 11, 10, 0)}, "zona horaria"),
        ({"evaluated_at": NOW + timedelta(days=2)}, "futuro"),
        ({"model_version": "  "}, "versión del modelo"),
    ],
)
def test_inconsistent_evaluation_is_rejected(overrides: dict, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        _record(**overrides)


def test_lesion_cannot_be_healthy_skin() -> None:
    with pytest.raises(ValidationError, match="no puede tener piel sana"):
        _record(
            probabilities=_probs(SANA),
            predicted_class="piel_sana",
            confidence=0.999538,
            clinical_codes=(),
        )


def test_clinical_code_must_be_mesh_or_ncbi() -> None:
    with pytest.raises(ValidationError, match="MeSH o NCBI"):
        ClinicalCode("http://venom.example", "123", "Mange")

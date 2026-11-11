import math
from dataclasses import dataclass

from bovi.clinical.domain.model.valueobjects.lesion_class import KNOWN_LABELS
from bovi.shared.domain.exceptions import ValidationError

# RF3: the probabilities of the model add up to 1 ± 0.01.
SUM_TOLERANCE = 0.01


@dataclass(frozen=True, slots=True)
class ClassProbability:
    label: str
    probability: float


@dataclass(frozen=True, slots=True)
class ClassProbabilities:
    """Output of the model for one photo (RNF17 keeps all of them)."""

    items: tuple[ClassProbability, ...]

    def __post_init__(self) -> None:
        labels = [item.label for item in self.items]
        if len(labels) < 2:
            raise ValidationError(
                "Envíe la probabilidad de cada clase del modelo.", code="probabilidades_invalidas"
            )
        if len(set(labels)) != len(labels):
            raise ValidationError(
                "Hay clases repetidas en las probabilidades.", code="probabilidades_invalidas"
            )
        unknown = sorted(set(labels) - KNOWN_LABELS)
        if unknown:
            raise ValidationError(
                f"Clase desconocida: {', '.join(unknown)}.", code="probabilidades_invalidas"
            )
        values = [item.probability for item in self.items]
        if any(not math.isfinite(v) or v < 0 or v > 1 for v in values):
            raise ValidationError(
                "Cada probabilidad debe estar entre 0 y 1.", code="probabilidades_invalidas"
            )
        if abs(sum(values) - 1) > SUM_TOLERANCE:
            raise ValidationError(
                "Las probabilidades deben sumar 1.", code="probabilidades_invalidas"
            )

    @property
    def top(self) -> ClassProbability:
        return max(self.items, key=lambda item: item.probability)

    def of(self, label: str) -> float | None:
        return next((i.probability for i in self.items if i.label == label), None)

    def to_json(self) -> list[dict[str, float | str]]:
        return [{"label": i.label, "probability": i.probability} for i in self.items]

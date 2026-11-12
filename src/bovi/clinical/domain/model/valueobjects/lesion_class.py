"""Labels the model can return (etiquetas.txt of every model version)."""

HEALTHY_LABELS = frozenset({"piel_sana", "sana"})  # "sana" is the label of the first models
DISEASE_LABELS = frozenset({"dermatofitosis", "papilomatosis", "sarna", "miasis"})
KNOWN_LABELS = HEALTHY_LABELS | DISEASE_LABELS


def is_healthy(label: str) -> bool:
    return label in HEALTHY_LABELS

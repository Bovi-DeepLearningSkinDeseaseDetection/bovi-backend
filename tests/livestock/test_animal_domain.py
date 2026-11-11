from datetime import UTC, datetime
from uuid import uuid4

import pytest

from bovi.livestock.domain.model.aggregates.animal import Animal
from bovi.livestock.domain.model.valueobjects.animal_sex import AnimalSex
from bovi.livestock.domain.model.valueobjects.ear_tag import EarTag
from bovi.shared.domain.exceptions import ValidationError

NOW = datetime(2026, 11, 11, 10, 0, tzinfo=UTC)


@pytest.mark.parametrize("text", ["pe 0012", "PE0012", "  pe0012 ", "p e 0 0 1 2"])
def test_ear_tag_is_normalized_like_the_app(text: str) -> None:
    assert EarTag(text) == EarTag("PE0012")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "Ingrese el número de arete."),
        ("A" * 21, "como máximo 20"),
        ("PE_0012", "letras, números y guiones"),
        ("PE/12", "letras, números y guiones"),
    ],
)
def test_invalid_ear_tag(text: str, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        EarTag(text)


def _animal(**overrides):
    values = {
        "id": uuid4(),
        "user_id": uuid4(),
        "ear_tag": "pe-0012",
        "breed": "  Brown   Swiss ",
        "sex": "female",
        "created_at": NOW,
    }
    values.update(overrides)
    return Animal.from_device(**values)


def test_animal_from_device_cleans_its_data() -> None:
    animal = _animal()

    assert animal.ear_tag.value == "PE-0012"
    assert animal.breed == "Brown Swiss"
    assert animal.sex is AnimalSex.FEMALE


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("sex", "hembra", "sexo_invalido"),
        ("breed", "   ", "raza_invalida"),
        ("breed", "x" * 51, "raza_invalida"),
        ("created_at", datetime(2026, 11, 11, 10, 0), "fecha_invalida"),
    ],
)
def test_invalid_animal(field: str, value: object, code: str) -> None:
    with pytest.raises(ValidationError) as error:
        _animal(**{field: value})
    assert error.value.code == code

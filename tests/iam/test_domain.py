from datetime import UTC, datetime

import pytest

from bovi.iam.domain.exceptions.iam_errors import ConsentRequiredError, InactiveUserError
from bovi.iam.domain.model.aggregates.user import User
from bovi.iam.domain.model.valueobjects.email_address import EmailAddress
from bovi.iam.domain.model.valueobjects.password import Password
from bovi.iam.domain.model.valueobjects.person_name import PersonName
from bovi.shared.domain.exceptions import ValidationError

NOW = datetime(2026, 11, 11, 10, 0, tzinfo=UTC)


def test_email_is_trimmed_and_lower_case() -> None:
    assert EmailAddress("  Juan.Perez@Example.COM ").value == "juan.perez@example.com"


@pytest.mark.parametrize("value", ["", "   ", "juan", "juan@", "@example.com", "ju an@x.com"])
def test_invalid_email_is_rejected(value: str) -> None:
    with pytest.raises(ValidationError) as error:
        EmailAddress(value)
    assert error.value.code == "correo_invalido"


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("abc12", "al menos 8 caracteres"),
        ("soloLetras", "una letra y un número"),
        ("12345678", "una letra y un número"),
        ("a1" + "x" * 80, "demasiado larga"),
    ],
)
def test_weak_password_is_rejected(value: str, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        Password(value)


def test_password_never_shows_in_repr() -> None:
    assert "establo2026" not in repr(Password("establo2026"))


def test_name_collapses_spaces() -> None:
    assert PersonName("  Juan   Pérez ").value == "Juan Pérez"


def test_name_too_short_is_rejected() -> None:
    with pytest.raises(ValidationError, match="nombre"):
        PersonName(" J ")


def _register(consent: bool) -> User:
    return User.register(
        name=PersonName("Juan Pérez"),
        email=EmailAddress("juan@example.com"),
        password_hash="hash",
        consent_accepted=consent,
        consent_version="2026.1",
        now=NOW,
    )


def test_register_keeps_the_consent_date_and_version() -> None:
    user = _register(consent=True)

    assert user.active
    assert user.consent_accepted_at == NOW
    assert user.consent_version == "2026.1"


def test_register_without_consent_is_rejected() -> None:
    # RNF7: Ley N.° 29733.
    with pytest.raises(ConsentRequiredError):
        _register(consent=False)


def test_inactive_user_cannot_sign_in() -> None:
    user = _register(consent=True)
    user.active = False

    with pytest.raises(InactiveUserError):
        user.ensure_can_sign_in()

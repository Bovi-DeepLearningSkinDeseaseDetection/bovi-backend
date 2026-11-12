import pytest
from pydantic import ValidationError

from bovi.shared.infrastructure.configuration.settings import Environment, Settings

DB_URL = "postgresql+psycopg://bovi:bovi@localhost:5432/bovi"
STRONG_SECRET = "x" * 32


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {"database_url": DB_URL, "jwt_secret": STRONG_SECRET}
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_defaults_follow_the_architecture() -> None:
    settings = _settings()

    assert settings.jwt_access_ttl_minutes == 60
    assert settings.jwt_refresh_ttl_days == 30
    assert settings.s3_region == "sa-east-1"
    assert settings.s3_upload_url_ttl_seconds == 15 * 60
    assert settings.s3_max_image_bytes == 512_000


def test_database_url_and_secret_are_required() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_production_rejects_a_short_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        _settings(app_env=Environment.PRODUCTION, jwt_secret="corto")


def test_production_rejects_a_local_s3_endpoint() -> None:
    with pytest.raises(ValidationError, match="S3_ENDPOINT_URL"):
        _settings(app_env=Environment.PRODUCTION, s3_endpoint_url="http://localhost:9000")


def test_production_accepts_strong_configuration() -> None:
    settings = _settings(app_env=Environment.PRODUCTION)

    assert settings.is_production

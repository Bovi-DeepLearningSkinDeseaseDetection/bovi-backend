"""Configuration read from environment variables (never from the code)."""

from enum import StrEnum
from functools import lru_cache

from fastapi import Request
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_MIN_SECRET_LENGTH = 32


class Environment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Environment = Environment.LOCAL
    log_level: str = "INFO"
    docs_enabled: bool = True

    database_url: str = Field(
        description="SQLAlchemy URL, for example postgresql+psycopg://user:pass@host:5432/bovi",
    )
    database_pool_size: int = 10
    database_max_overflow: int = 10
    # Fail fast instead of hanging when PostgreSQL does not answer (health check, RNF15).
    database_connect_timeout_seconds: int = 5

    jwt_secret: str = Field(min_length=1)
    jwt_access_ttl_minutes: int = 60
    jwt_refresh_ttl_days: int = 30
    jwt_issuer: str = "bovi-api"
    # Cost of bcrypt: 12 in production; tests lower it to stay fast.
    bcrypt_rounds: int = Field(default=12, ge=4, le=16)
    # Edition of the data consent text the app shows on sign up (Ley N.° 29733).
    consent_version: str = "2026.1"

    s3_bucket: str = "bovi-evaluaciones"
    s3_region: str = "sa-east-1"
    # Only for the local S3 emulator; empty in AWS.
    s3_endpoint_url: str | None = None
    s3_upload_url_ttl_seconds: int = 900
    s3_download_url_ttl_seconds: int = 900
    s3_max_image_bytes: int = 512_000

    @property
    def is_production(self) -> bool:
        return self.app_env is Environment.PRODUCTION

    @model_validator(mode="after")
    def _check_production_secrets(self) -> "Settings":
        if self.is_production and len(self.jwt_secret) < _MIN_SECRET_LENGTH:
            raise ValueError(
                f"JWT_SECRET must have at least {_MIN_SECRET_LENGTH} characters in production."
            )
        if self.is_production and self.bcrypt_rounds < 12:
            raise ValueError("BCRYPT_ROUNDS must be at least 12 in production.")
        if self.is_production and self.s3_endpoint_url:
            raise ValueError("S3_ENDPOINT_URL is only for local development.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_app_settings(request: Request) -> Settings:
    """Settings the running app was created with (tests pass their own)."""
    return request.app.state.settings

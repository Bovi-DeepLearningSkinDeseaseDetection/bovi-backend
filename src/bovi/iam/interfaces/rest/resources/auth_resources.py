from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SignUpResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Juan Pérez",
                "email": "juan.perez@example.com",
                "password": "establo2026",
                "consent_accepted": True,
            }
        }
    )

    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=200)
    consent_accepted: bool = Field(
        description="El ganadero aceptó el consentimiento de tratamiento de datos (Ley N.° 29733)"
    )


class SignInResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "juan.perez@example.com", "password": "establo2026"}
        }
    )

    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=200)


class RefreshSessionResource(BaseModel):
    refresh_token: str = Field(min_length=1)


class UserResource(BaseModel):
    id: UUID
    name: str
    email: str


class SessionResource(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(description="Segundos de validez del access token")
    refresh_expires_in: int = Field(description="Segundos de validez del refresh token")
    user: UserResource

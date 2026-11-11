from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnimalSyncItemResource(BaseModel):
    """Animal as stored on the phone (Animal of the app)."""

    id: UUID = Field(description="uuid del animal generado en el celular")
    ear_tag: str = Field(
        max_length=100, description="Arete; se normaliza sin espacios y en mayúsculas"
    )
    breed: str = Field(max_length=100)
    sex: str = Field(max_length=20, description="female | male")
    created_at: datetime = Field(description="Fecha de registro en el celular, con zona horaria")


class AnimalSyncBatchResource(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "animals": [
                    {
                        "id": "0f8b7c1e-2a52-4c4f-9a43-6f1d2b9c1a01",
                        "ear_tag": "PE-0012",
                        "breed": "Holstein",
                        "sex": "female",
                        "created_at": "2026-11-10T09:30:00-05:00",
                    }
                ]
            }
        }
    )

    animals: list[AnimalSyncItemResource]

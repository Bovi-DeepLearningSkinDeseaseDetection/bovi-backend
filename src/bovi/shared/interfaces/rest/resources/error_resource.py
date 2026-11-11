from pydantic import BaseModel, Field


class FieldErrorResource(BaseModel):
    field: str = Field(description="Ruta del campo con error, por ejemplo evaluations[0].uuid")
    message: str = Field(description="Mensaje en español para el usuario")


class ErrorResource(BaseModel):
    """Body of every error response of the API."""

    code: str = Field(description="Código estable para que la app decida qué hacer")
    message: str = Field(description="Mensaje en español para el usuario")
    details: list[FieldErrorResource] = Field(default_factory=list)

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Base


class EvaluationEntity(Base):
    """Table `evaluacion`: one row per photo analyzed on the phone. Never updated."""

    __tablename__ = "evaluacion"
    # Restoring the history goes by farmer and newest first (HU13).
    __table_args__ = (Index("ix_evaluacion_usuario_fecha", "usuario_id", "fecha_hora"),)

    # Generated on the phone; it is also the idempotency key (RNF10).
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    # By table name: clinical does not import the entities of iam nor livestock.
    usuario_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("usuario.id"))
    animal_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("animal.id"), index=True)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    zona_corporal: Mapped[str | None] = mapped_column(String(10))
    resultado: Mapped[str] = mapped_column(String(15))
    clase_predicha: Mapped[str] = mapped_column(String(30))
    confianza: Mapped[float] = mapped_column(Float)
    probabilidades: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    codigos_clinicos: Mapped[list[dict[str, str]]] = mapped_column(JSONB)
    version_catalogo: Mapped[str | None] = mapped_column(String(20))
    version_modelo: Mapped[str] = mapped_column(String(50))
    tiempo_inferencia_ms: Mapped[int | None] = mapped_column(Integer)
    origen_imagen: Mapped[str] = mapped_column(String(10))
    clave_imagen: Mapped[str] = mapped_column(String(200))
    sincronizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

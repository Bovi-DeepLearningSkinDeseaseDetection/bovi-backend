from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Base


class UserEntity(Base):
    """Table `usuario`: one row per farmer (column names in Spanish)."""

    __tablename__ = "usuario"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    correo: Mapped[str] = mapped_column(String(254), unique=True)
    hash_contrasena: Mapped[str] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    consentimiento_aceptado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consentimiento_version: Mapped[str] = mapped_column(String(20))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

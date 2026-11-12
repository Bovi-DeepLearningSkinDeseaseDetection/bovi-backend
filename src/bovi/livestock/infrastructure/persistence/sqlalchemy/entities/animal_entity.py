from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Base


class AnimalEntity(Base):
    """Table `animal`. The ear tag is unique per farmer; that index also serves usuario_id."""

    __tablename__ = "animal"
    __table_args__ = (UniqueConstraint("usuario_id", "arete"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    # By table name: livestock does not import the entities of iam.
    usuario_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("usuario.id"))
    arete: Mapped[str] = mapped_column(String(20))
    raza: Mapped[str] = mapped_column(String(50))
    sexo: Mapped[str] = mapped_column(String(10))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sincronizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

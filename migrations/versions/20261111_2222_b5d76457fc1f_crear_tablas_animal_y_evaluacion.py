"""crear tablas animal y evaluacion

Revision ID: b5d76457fc1f
Revises: 7cdee1980468
Create Date: 2026-11-11 22:22:53.250463+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b5d76457fc1f"
down_revision: str | None = "7cdee1980468"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "animal",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("arete", sa.String(length=20), nullable=False),
        sa.Column("raza", sa.String(length=50), nullable=False),
        sa.Column("sexo", sa.String(length=10), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "sincronizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuario.id"], name=op.f("fk_animal_usuario_id_usuario")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_animal")),
        sa.UniqueConstraint("usuario_id", "arete", name=op.f("uq_animal_usuario_id_arete")),
    )
    op.create_table(
        "evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("animal_id", sa.Uuid(), nullable=True),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("zona_corporal", sa.String(length=10), nullable=True),
        sa.Column("resultado", sa.String(length=15), nullable=False),
        sa.Column("clase_predicha", sa.String(length=30), nullable=False),
        sa.Column("confianza", sa.Float(), nullable=False),
        sa.Column("probabilidades", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("codigos_clinicos", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("version_catalogo", sa.String(length=20), nullable=True),
        sa.Column("version_modelo", sa.String(length=50), nullable=False),
        sa.Column("tiempo_inferencia_ms", sa.Integer(), nullable=True),
        sa.Column("origen_imagen", sa.String(length=10), nullable=False),
        sa.Column("clave_imagen", sa.String(length=200), nullable=False),
        sa.Column(
            "sincronizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["animal_id"], ["animal.id"], name=op.f("fk_evaluacion_animal_id_animal")
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuario.id"], name=op.f("fk_evaluacion_usuario_id_usuario")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluacion")),
    )
    op.create_index(op.f("ix_evaluacion_animal_id"), "evaluacion", ["animal_id"], unique=False)
    op.create_index(
        "ix_evaluacion_usuario_fecha", "evaluacion", ["usuario_id", "fecha_hora"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_evaluacion_usuario_fecha", table_name="evaluacion")
    op.drop_index(op.f("ix_evaluacion_animal_id"), table_name="evaluacion")
    op.drop_table("evaluacion")
    op.drop_table("animal")

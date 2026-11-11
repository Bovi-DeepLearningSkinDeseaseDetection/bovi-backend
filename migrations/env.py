"""Alembic environment: one metadata for every bounded context."""

import importlib
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from bovi.shared.infrastructure.configuration.settings import get_settings
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Base

# Each bounded context registers its ORM entities in the __init__ of this package.
ENTITY_PACKAGES = [
    "bovi.iam.infrastructure.persistence.sqlalchemy.entities",
    "bovi.livestock.infrastructure.persistence.sqlalchemy.entities",
    "bovi.clinical.infrastructure.persistence.sqlalchemy.entities",
]
for package in ENTITY_PACKAGES:
    importlib.import_module(package)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The URL comes from DATABASE_URL unless the caller already set one (tests do).
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

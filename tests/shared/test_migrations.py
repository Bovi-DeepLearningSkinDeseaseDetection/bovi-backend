"""The migration chain applies and reverts cleanly on PostgreSQL."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from bovi.shared.infrastructure.configuration.settings import Settings
from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Database

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_migrations_upgrade_and_downgrade(settings: Settings, database: Database) -> None:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")

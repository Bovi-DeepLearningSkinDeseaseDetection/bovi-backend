"""The migration chain applies and reverts cleanly on PostgreSQL."""

import pytest
from alembic import command

from bovi.shared.infrastructure.persistence.sqlalchemy.configuration.database import Database
from tests.conftest import alembic_config


@pytest.mark.integration
def test_migrations_upgrade_and_downgrade(database: Database) -> None:
    config = alembic_config()

    command.downgrade(config, "base")
    command.upgrade(config, "head")

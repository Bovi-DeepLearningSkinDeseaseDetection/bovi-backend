"""SQLAlchemy engine, declarative base and session per request."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from bovi.shared.infrastructure.configuration.settings import Settings

# Stable constraint names, so Alembic autogenerate produces repeatable migrations.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base of every ORM entity of every bounded context."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Database:
    """Owns the connection pool to PostgreSQL."""

    def __init__(self, settings: Settings) -> None:
        self.engine: Engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            connect_args={"connect_timeout": settings.database_connect_timeout_seconds},
        )
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False)

    def ping(self) -> None:
        """Raises when PostgreSQL cannot be reached."""
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def dispose(self) -> None:
        self.engine.dispose()


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_session(request: Request) -> Iterator[Session]:
    """One session per request; rolled back if the request fails.

    Application services decide when to commit, so a use case is one unit of work.
    """
    session = get_database(request).session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

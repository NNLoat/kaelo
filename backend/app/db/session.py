from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

settings = get_settings()

# Sync engine using the psycopg (v3) driver.
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_pre_ping=True,
)


def init_db() -> None:
    """Create all tables directly from model metadata.

    Schema in real environments is managed by Alembic migrations
    (``alembic upgrade head``). This helper bypasses migrations and is intended
    only for tests or throwaway local databases where speed matters more than
    migration fidelity.
    """
    # Import models so they register on SQLModel.metadata before create_all.
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    with Session(engine) as session:
        yield session

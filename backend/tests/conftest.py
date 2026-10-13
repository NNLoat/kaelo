"""Pytest fixtures for backend tests.

A throwaway ``postgres:17`` container is started once per test session via
`testcontainers`. Its lifecycle is owned entirely by the test run — it never
appears in, or is triggered by, the dev ``compose.yaml``. Each test runs inside
an outer transaction that is rolled back on teardown, so tests are isolated and
the database state never leaks between them.

Requires a reachable Docker daemon (true locally and in most CI).
"""

import os

# Disable testcontainers' Ryuk reaper sidecar. Ryuk bind-mounts the Docker
# socket, which some runtimes (e.g. Colima on macOS) do not permit. We rely on
# the ``with PostgresContainer(...)`` context managers for deterministic
# cleanup instead. Set before importing testcontainers so it takes effect.
os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")

# The app requires SESSION_SECRET (no default) to construct Settings. Provide a
# throwaway value for the test process before app.main is imported below.
os.environ.setdefault("SESSION_SECRET", "test-session-secret")

from collections.abc import Generator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402
from testcontainers.community.postgres import PostgresContainer  # noqa: E402

# Import models so they register on SQLModel.metadata before create_all.
from app import models  # noqa: E402, F401
from app.db.session import get_session  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer]:
    """Start one disposable postgres:17 container for the whole test session."""
    with PostgresContainer(
        "postgres:17",
        username="test",
        password="test",
        dbname="test",
        driver="psycopg",  # SQLAlchemy URL uses postgresql+psycopg://
    ) as container:
        yield container


@pytest.fixture(scope="session")
def engine(postgres_container: PostgresContainer) -> Generator[Engine]:
    """SQLModel engine bound to the test container, with schema created once.

    Tests use ``create_all`` for speed. Alembic migrations are exercised
    separately (see test_migrations.py) rather than on every test run.
    """
    eng = create_engine(postgres_container.get_connection_url(), pool_pre_ping=True)
    SQLModel.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine: Engine) -> Generator[Session]:
    """A session wrapped in an outer transaction that is rolled back per test.

    The connection opens a transaction and the Session joins it in
    ``create_savepoint`` mode: the endpoint under test may ``commit()`` or
    ``rollback()`` freely (those act on a SAVEPOINT), while the outer
    transaction is rolled back on teardown — discarding everything the test
    wrote and keeping tests isolated.
    """
    connection = engine.connect()
    transaction = connection.begin()
    sess = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield sess

    sess.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(session: Session) -> Generator[TestClient]:
    """FastAPI TestClient with the DB dependency overridden to the test session."""

    def override_get_session() -> Generator[Session]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

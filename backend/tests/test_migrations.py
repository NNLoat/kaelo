"""Migration-safety test.

Runs the full Alembic chain (upgrade head -> downgrade base -> upgrade head)
against a clean throwaway database to catch migrations that fail to apply or
fail to reverse. This is cheap insurance that every revision in
``alembic/versions/`` is actually runnable.
"""

from alembic.config import Config
from sqlalchemy import create_engine, inspect
from testcontainers.community.postgres import PostgresContainer

from alembic import command


def _alembic_config(db_url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_migrations_upgrade_and_downgrade() -> None:
    # Fresh container so we start from a truly empty schema, independent of the
    # session-scoped engine used by the API tests.
    with PostgresContainer(
        "postgres:17",
        username="test",
        password="test",
        dbname="test",
        driver="psycopg",
    ) as container:
        db_url = container.get_connection_url()
        cfg = _alembic_config(db_url)
        engine = create_engine(db_url)

        # Up to latest: the items table should exist.
        command.upgrade(cfg, "head")
        assert "items" in inspect(engine).get_table_names()

        # All the way back down: items should be gone.
        command.downgrade(cfg, "base")
        assert "items" not in inspect(engine).get_table_names()

        # And back up again, to be sure it's repeatable.
        command.upgrade(cfg, "head")
        assert "items" in inspect(engine).get_table_names()

        engine.dispose()


def test_users_table_and_unique_username_index() -> None:
    """After upgrade, the users table exists with a unique index on username."""
    with PostgresContainer(
        "postgres:17",
        username="test",
        password="test",
        dbname="test",
        driver="psycopg",
    ) as container:
        db_url = container.get_connection_url()
        cfg = _alembic_config(db_url)
        engine = create_engine(db_url)

        command.upgrade(cfg, "head")
        inspector = inspect(engine)
        assert "users" in inspector.get_table_names()
        username_indexes = [
            ix for ix in inspector.get_indexes("users") if ix["column_names"] == ["username"]
        ]
        assert any(ix["unique"] for ix in username_indexes)

        command.downgrade(cfg, "base")
        assert "users" not in inspect(engine).get_table_names()

        command.upgrade(cfg, "head")
        assert "users" in inspect(engine).get_table_names()

        engine.dispose()

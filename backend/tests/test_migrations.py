"""Migration-safety test.

Runs the full Alembic chain (upgrade head -> downgrade base -> upgrade head)
against a clean throwaway database to catch migrations that fail to apply or
fail to reverse. This is cheap insurance that every revision in
``alembic/versions/`` is actually runnable.
"""

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from testcontainers.community.postgres import PostgresContainer


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

        # The papers table and its de-dup / search indexes exist after upgrade.
        tables = inspect(engine).get_table_names()
        assert "papers" in tables
        index_names = {ix["name"] for ix in inspect(engine).get_indexes("papers")}
        assert {"ix_papers_title", "ix_papers_doi", "ix_papers_arxiv_id"} <= index_names

        # All the way back down: items should be gone.
        command.downgrade(cfg, "base")
        assert "items" not in inspect(engine).get_table_names()

        # And back up again, to be sure it's repeatable.
        command.upgrade(cfg, "head")
        assert "items" in inspect(engine).get_table_names()
        assert "papers" in inspect(engine).get_table_names()

        engine.dispose()


def test_settings_requires_bedrock_model_id(monkeypatch) -> None:
    """Constructing Settings without BEDROCK_MODEL_ID must fail (no committed
    default, R9.6)."""
    import pydantic
    import pytest

    from app.core.config import Settings

    monkeypatch.delenv("BEDROCK_MODEL_ID", raising=False)
    with pytest.raises(pydantic.ValidationError):
        Settings(_env_file=None)

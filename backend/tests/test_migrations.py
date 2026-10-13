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


def test_reproducibility_tables_and_unique_indexes() -> None:
    """After upgrade, both repro tables exist with unique paper_id indexes; the
    full upgrade -> downgrade -> upgrade cycle is repeatable (R7.3, R7.4)."""
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
        tables = inspector.get_table_names()
        assert "reproducibility_scores" in tables
        assert "experiment_setups" in tables
        for table in ("reproducibility_scores", "experiment_setups"):
            paper_id_indexes = [
                ix for ix in inspector.get_indexes(table) if ix["column_names"] == ["paper_id"]
            ]
            assert any(ix["unique"] for ix in paper_id_indexes)

        command.downgrade(cfg, "base")
        assert "reproducibility_scores" not in inspect(engine).get_table_names()

        command.upgrade(cfg, "head")
        assert "reproducibility_scores" in inspect(engine).get_table_names()

        engine.dispose()


def test_settings_rejects_non_https_github_api_base(monkeypatch) -> None:
    """A non-HTTPS github_api_base is rejected at startup (R1.6)."""
    import pydantic
    import pytest

    from app.core.config import Settings

    with pytest.raises(pydantic.ValidationError):
        Settings(_env_file=None, github_api_base="http://api.github.com")


def test_generation_tables_and_partial_unique_indexes() -> None:
    """After upgrade, both generation tables exist with the two hand-added
    partial unique indexes; the upgrade -> downgrade -> upgrade cycle is
    repeatable (R8.1, R8.4, R5.6)."""
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
        tables = inspector.get_table_names()
        assert "generation_jobs" in tables
        assert "generations" in tables

        job_indexes = {ix["name"] for ix in inspector.get_indexes("generation_jobs")}
        gen_indexes = {ix["name"] for ix in inspector.get_indexes("generations")}
        assert "uq_generation_jobs_inflight" in job_indexes
        assert "uq_generations_latest" in gen_indexes
        # Both are unique.
        assert any(
            ix["name"] == "uq_generation_jobs_inflight" and ix["unique"]
            for ix in inspector.get_indexes("generation_jobs")
        )
        assert any(
            ix["name"] == "uq_generations_latest" and ix["unique"]
            for ix in inspector.get_indexes("generations")
        )

        command.downgrade(cfg, "base")
        assert "generation_jobs" not in inspect(engine).get_table_names()

        command.upgrade(cfg, "head")
        assert "generations" in inspect(engine).get_table_names()

        engine.dispose()

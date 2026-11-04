from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Connection string, e.g. postgresql+psycopg://app:app@db:5432/app
    database_url: str = "postgresql+psycopg://app:app@db:5432/app"

    # CORS origins allowed to call the API (the frontend dev server).
    cors_origins: list[str] = ["http://localhost:5173"]

    # Echo SQL to the logs — handy during development.
    db_echo: bool = False

    # Ranking weights for the non-AI Final Score blend (R5.7, R8.5).
    relevance_weight: float = 0.3
    reproducibility_weight: float = 0.7

    # Source scope + limits (R7.2).
    source_domains: list[str] = ["computer science", "medicine"]
    source_result_limit: int = 25
    source_timeout_seconds: float = 10.0

    # Bedrock / LangChain (R8.6, R9.6). bedrock_model_id has NO default, so the
    # app fails to start if it is absent rather than reading a committed value.
    bedrock_model_id: str
    aws_region: str = "us-east-1"
    llm_timeout_seconds: float = 20.0

    # Max output tokens for code/review generation. Without an explicit cap the
    # Bedrock default is low and long REVIEW.md / generated files get truncated
    # mid-output. Env-overridable per model's context limit.
    codegen_max_tokens: int = 8192

    # code-generation: fail a job still running past this bound (R7.6).
    codegen_job_timeout_seconds: int = 600

    # code-generation: when true, generation returns a canned artifact without
    # calling Bedrock — deterministic dev/test flow (R10). Off by default.
    codegen_mock: bool = False

    # paper-search: when false, skip the LLM query rewrite and send the raw query
    # to the sources, so retrieval is repeatable (demo). On by default (R8.2).
    query_expansion_enabled: bool = True

    # demo-mode: off = normal; record = live calls are saved to the Cassette;
    # replay = calls are answered from it (a miss falls back to live).
    demo_mode: Literal["off", "record", "replay"] = "off"
    demo_cassette_path: str = "demo/fixtures/cassette.json"

    # Signs session cookies. REQUIRED — no default, so a missing value fails
    # startup rather than reading a secret from committed source (R7.6).
    session_secret: str

    # Session cookie max-age; defaults to one day.
    session_ttl_seconds: int = 60 * 60 * 24

    # Mark the session cookie Secure (HTTPS-only); enable in production.
    cookie_secure: bool = False

    # GitHub repo inspection (R1.6). github_token is a SECRET — env only, no
    # committed default; absence degrades to unauthenticated access.
    github_api_base: str = "https://api.github.com"
    github_token: str | None = None
    repo_recency_days: int = 365
    repo_inspect_timeout_seconds: float = 10.0

    # Reproducibility blend weights (non-AI, R4.2).
    repro_repo_weight: float = 0.5
    repro_setup_weight: float = 0.5

    # writer-workspace extraction/unpack limits (not secrets; safe defaults).
    max_manuscript_bytes: int = 25 * 1024 * 1024  # 25 MiB
    max_source_archive_bytes: int = 50 * 1024 * 1024  # 50 MiB
    max_source_total_bytes: int = 100 * 1024 * 1024  # 100 MiB unpacked
    max_source_files: int = 5000
    git_fetch_timeout_seconds: int = 60

    @field_validator("github_api_base")
    @classmethod
    def _github_api_base_https(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("github_api_base must be HTTPS")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()

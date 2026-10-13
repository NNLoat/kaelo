from functools import lru_cache

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
    relevance_weight: float = 0.7
    reproducibility_weight: float = 0.3

    # Source scope + limits (R7.2).
    source_domains: list[str] = ["computer science", "medicine"]
    source_result_limit: int = 25
    source_timeout_seconds: float = 10.0

    # Bedrock / LangChain (R8.6, R9.6). bedrock_model_id has NO default, so the
    # app fails to start if it is absent rather than reading a committed value.
    bedrock_model_id: str
    aws_region: str = "us-east-1"
    llm_timeout_seconds: float = 20.0


@lru_cache
def get_settings() -> Settings:
    return Settings()

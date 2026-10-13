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

    # Signs session cookies. REQUIRED — no default, so a missing value fails
    # startup rather than reading a secret from committed source (R7.6).
    session_secret: str

    # Session cookie max-age; defaults to one day.
    session_ttl_seconds: int = 60 * 60 * 24

    # Mark the session cookie Secure (HTTPS-only); enable in production.
    cookie_secure: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Config smoke test: SESSION_SECRET is required (no committed default)."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_requires_session_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    # Avoid picking the value up from a local .env file during the test.
    monkeypatch.setattr(Settings, "model_config", {**Settings.model_config, "env_file": None})
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]

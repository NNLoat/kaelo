"""demo-mode settings and startup log (spec demo-mode, task 1)."""

import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import main
from app.core.config import Settings


def _settings(monkeypatch, **env: str) -> Settings:
    for key in ("DEMO_MODE", "DEMO_CASSETTE_PATH"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return Settings(_env_file=None)


def test_defaults_are_off_and_documented_path(monkeypatch) -> None:
    s = _settings(monkeypatch)
    assert s.demo_mode == "off"
    assert s.demo_cassette_path == "demo/fixtures/cassette.json"


@pytest.mark.parametrize("mode", ["off", "record", "replay"])
def test_accepts_the_three_modes(monkeypatch, mode: str) -> None:
    assert _settings(monkeypatch, DEMO_MODE=mode).demo_mode == mode


def test_bogus_mode_fails_and_names_setting_and_values(monkeypatch) -> None:
    with pytest.raises(ValidationError) as exc:
        _settings(monkeypatch, DEMO_MODE="bogus")
    text = str(exc.value)
    assert "demo_mode" in text
    for accepted in ("off", "record", "replay"):
        assert accepted in text


@pytest.mark.parametrize("mode,logged", [("off", False), ("record", True), ("replay", True)])
def test_startup_log_only_when_not_off(monkeypatch, caplog, mode: str, logged: bool) -> None:
    monkeypatch.setattr(main, "settings", _settings(monkeypatch, DEMO_MODE=mode))
    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        with TestClient(main.app):
            pass
    lines = [r.getMessage() for r in caplog.records if r.getMessage().startswith("demo mode=")]
    assert bool(lines) is logged
    if logged:
        assert lines == [f"demo mode={mode} cassette=demo/fixtures/cassette.json"]

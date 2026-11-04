"""Shared helpers for the demo-mode tests."""

import logging
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from app.core.config import get_settings
from app.services.demo import cassette


@contextmanager
def demo(mode: str, path: Path):
    """Run with Demo_Mode ``mode`` and a Cassette at ``path`` (fresh store)."""
    s = get_settings().model_copy(update={"demo_mode": mode, "demo_cassette_path": str(path)})
    with mock.patch.object(cassette, "get_settings", lambda: s):
        cassette.reset_store()
        try:
            yield
        finally:
            cassette.reset_store()


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.messages: list[str] = []

    def emit(self, record):
        if record.levelno >= logging.WARNING:
            self.messages.append(record.getMessage())


@contextmanager
def captured_warnings():
    handler = _Capture()
    cassette.log.addHandler(handler)
    try:
        yield handler.messages
    finally:
        cassette.log.removeHandler(handler)

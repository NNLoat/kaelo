"""Cassette store and the off/record/replay state machine for demo-mode.

No FastAPI, SQLModel or domain imports: the seam wrappers (``seams.py``) supply
the codecs. See specs/demo-mode/design.md.
"""

import hashlib
import json
import logging
import os
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.core.config import get_settings

log = logging.getLogger(__name__)

VERSION = 1


class CassetteError(Exception):
    """The Cassette is unreadable, unsupported, or an entry would leak a secret."""


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def request_key(seam: str, key_input: dict) -> str:
    """``"<seam>:<sha256 hex>"`` of the canonical input (independent of dict order)."""
    digest = hashlib.sha256(_canonical(key_input).encode("utf-8")).hexdigest()
    return f"{seam}:{digest}"


def _secrets() -> list[str]:
    settings = get_settings()
    values = (
        os.environ.get("AWS_SECRET_ACCESS_KEY"),
        settings.github_token,
        settings.session_secret,
    )
    return [v for v in values if v]


class CassetteStore:
    """One JSON file: ``{"version": 1, "entries": {"<seam>:<digest>": {...}}}``."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._lock = threading.RLock()
        self._entries: dict[str, dict] | None = None

    def _load(self) -> dict[str, dict]:
        if self._entries is not None:
            return self._entries
        try:
            raw = self.path.read_bytes()
        except FileNotFoundError:
            self._entries = {}
            return self._entries
        try:
            doc = json.loads(raw.decode("utf-8"))
        except ValueError as exc:  # bad UTF-8 or bad JSON
            raise CassetteError(f"cassette {self.path} is not valid JSON: {exc}") from exc
        if not isinstance(doc, dict) or doc.get("version") != VERSION:
            raise CassetteError(f"cassette {self.path} has an unsupported format or version")
        entries = doc.get("entries")
        if not isinstance(entries, dict):
            raise CassetteError(f"cassette {self.path} has no entries mapping")
        self._entries = entries
        return entries

    def get(self, key: str) -> dict | None:
        with self._lock:
            return self._load().get(key)

    def put(self, key: str, entry: dict) -> None:
        with self._lock:
            entries = self._load()  # raises on a corrupt file before any write
            text = _canonical(entry)
            for secret in _secrets():
                # Also test the JSON-escaped form: quotes/backslashes are escaped in text.
                if secret in text or json.dumps(secret, ensure_ascii=False)[1:-1] in text:
                    raise CassetteError(
                        f"refusing to record {key}: entry contains a configured secret"
                    )
            updated = {**entries, key: entry}
            self._write(updated)
            self._entries = updated

    def _write(self, entries: dict[str, dict]) -> None:
        doc = {"version": VERSION, "entries": entries}
        data = json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.path)


_store: CassetteStore | None = None
_store_lock = threading.Lock()


def get_store() -> CassetteStore:
    """The process-wide store for the configured path (rebuilt if the path changes)."""
    global _store
    path = Path(get_settings().demo_cassette_path)
    with _store_lock:
        if _store is None or _store.path != path:
            _store = CassetteStore(path)
        return _store


def reset_store() -> None:
    global _store
    with _store_lock:
        _store = None


def cached(
    seam: str,
    key_input: dict,
    live: Callable[[], Any],
    encode: Callable[[Any], Any],
    decode: Callable[[Any], Any],
    label: str = "",
    model: str | None = None,
) -> Any:
    """Run ``live`` under the configured Demo_Mode (off / record / replay)."""
    mode = get_settings().demo_mode
    if mode == "off":
        return live()

    key = request_key(seam, key_input)
    store = get_store()

    if mode == "replay":
        entry = store.get(key)
        if entry is not None:
            return decode(entry["recorded"])
        # Seam and digest only: never the label or prompt text.
        log.warning("demo replay miss seam=%s key=%s", seam, key.split(":", 1)[1])
        return live()

    result = live()  # record: a raising live call propagates and stores nothing
    entry = {"seam": seam, "label": label, "recorded": encode(result)}
    if model:
        entry["model"] = model
    store.put(key, entry)
    return result

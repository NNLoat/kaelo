"""Property tests for the demo-mode Cassette and cached() (spec demo-mode, task 2).

No network, Bedrock or GitHub: every ``live`` is a local function. A ``live`` that
must not run raises AssertionError.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.config import get_settings
from app.services.demo import cassette
from app.services.demo.cassette import CassetteError, CassetteStore, cached, request_key
from tests.demo_helpers import captured_warnings, demo

_scalars = st.none() | st.booleans() | st.integers() | st.text()
_json = st.recursive(
    _scalars,
    lambda c: st.lists(c, max_size=3) | st.dictionaries(st.text(), c, max_size=3),
    max_leaves=6,
)
# Real secrets live in environment variables, which cannot contain NUL.
_secret_text = st.text(
    alphabet=st.characters(exclude_characters="\x00", exclude_categories=["Cs"]), min_size=1
)
_key_inputs = st.dictionaries(st.text(), _scalars, max_size=5)
_seams = st.sampled_from(["llm", "source", "repo"])
_entries = st.fixed_dictionaries({"seam": _seams, "label": st.text(), "recorded": _json})

_FAIL = AssertionError("live call must not run")


def _must_not_run():
    raise _FAIL


def _identity(x):
    return x


# --- Property 1 ---------------------------------------------------------------


# Feature: demo-mode, Property 1: Request keys are canonical
@settings(max_examples=100)
@given(seam=_seams, d=_key_inputs)
def test_key_ignores_insertion_order(seam, d) -> None:
    assert request_key(seam, d) == request_key(seam, dict(reversed(list(d.items()))))


# Feature: demo-mode, Property 1: Request keys are canonical
@settings(max_examples=100)
@given(seam=_seams, a=_key_inputs, b=_key_inputs)
def test_distinct_inputs_give_distinct_keys(seam, a, b) -> None:
    if a != b:
        assert request_key(seam, a) != request_key(seam, b)
    assert request_key("llm", a) != request_key("repo", a)


def test_key_format_is_pinned() -> None:
    # sha256 of '{"n":1,"prompt":"hi"}' (checked with sha256sum): the key format is a contract.
    assert request_key("llm", {"prompt": "hi", "n": 1}) == (
        "llm:133a4fcfcb20d59a314320cacb6d9a190de433e6402e40cf7d5156f7b165a421"
    )


# --- Property 2 ---------------------------------------------------------------


# Feature: demo-mode, Property 2: Cassette serialization round-trips and is byte-stable
@settings(max_examples=100)
@given(entries=st.dictionaries(st.text(min_size=1), _entries, min_size=1, max_size=6))
def test_round_trip_and_byte_stable(entries) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        a, b = Path(tmp) / "a.json", Path(tmp) / "b.json"
        sa, sb = CassetteStore(a), CassetteStore(b)
        for k, v in entries.items():
            sa.put(k, v)
        for k, v in reversed(list(entries.items())):
            sb.put(k, v)
        assert a.read_bytes() == b.read_bytes()
        reloaded = CassetteStore(a)
        assert {k: reloaded.get(k) for k in entries} == entries


# --- Properties 3-7 -----------------------------------------------------------


# Feature: demo-mode, Property 3: Record then replay returns the recorded result with no live call
@settings(max_examples=100)
@given(seam=_seams, key_input=_key_inputs, result=_json)
def test_record_then_replay(seam, key_input, result) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "c.json"
        with demo("record", path):
            assert cached(seam, key_input, lambda: result, _identity, _identity) == result
        assert path.exists()
        with demo("replay", path):  # fresh store: proves the entry came from the file
            assert cached(seam, key_input, _must_not_run, _identity, _identity) == result


# Feature: demo-mode, Property 4: A replay miss falls through, logs once, and writes nothing
@settings(max_examples=100)
@given(known=_key_inputs, other=_key_inputs, text=st.text(), result=_json)
def test_replay_miss_goes_live_once_and_writes_nothing(known, other, text, result) -> None:
    known = {**known, "k": "known"}
    other = {**other, "k": "other", "prompt": "ZZPROMPTZZ" + text}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "c.json"
        with demo("record", path):
            cached("llm", known, lambda: "x", _identity, _identity, label="ZZPROMPTZZ")
        before = path.read_bytes()
        calls: list[int] = []

        def live():
            calls.append(1)
            return result

        with demo("replay", path), captured_warnings() as warnings:
            assert cached("llm", other, live, _identity, _identity, label="ZZPROMPTZZ") == result
        assert calls == [1]
        assert path.read_bytes() == before
        digest = request_key("llm", other).split(":", 1)[1]
        assert len(warnings) == 1
        assert "llm" in warnings[0] and digest in warnings[0]
        assert "ZZPROMPTZZ" not in warnings[0]


# Feature: demo-mode, Property 5: A failed live call in record is propagated and never recorded
@settings(max_examples=100)
@given(key_input=_key_inputs, message=st.text())
def test_failed_live_call_is_not_recorded(key_input, message) -> None:
    boom = RuntimeError(message)

    def live():
        raise boom

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "c.json"
        with demo("record", path):
            with pytest.raises(RuntimeError) as exc:
                cached("llm", key_input, live, _identity, _identity)
            assert exc.value is boom
            assert cassette.get_store().get(request_key("llm", key_input)) is None
        assert not path.exists()


# Feature: demo-mode, Property 6: Re-recording replaces
@settings(max_examples=100)
@given(key_input=_key_inputs, first=_json, second=_json, other=_json)
def test_rerecord_replaces(key_input, first, second, other) -> None:
    key_input = {**key_input, "k": "target"}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "c.json"
        with demo("record", path):
            cached("llm", {"k": "neighbour"}, lambda: other, _identity, _identity)
            cached("llm", key_input, lambda: first, _identity, _identity)
            cached("llm", key_input, lambda: second, _identity, _identity)
        entries = json.loads(path.read_text())["entries"]
        key = request_key("llm", key_input)
        assert len(entries) == 2
        assert entries[key]["recorded"] == second
        assert entries[request_key("llm", {"k": "neighbour"})]["recorded"] == other


# Feature: demo-mode, Property 7: Off is transparent
@settings(max_examples=100)
@given(seam=_seams, key_input=_key_inputs, result=_json)
def test_off_never_touches_the_cassette(seam, key_input, result) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sub" / "c.json"
        with demo("off", path), mock.patch.object(cassette, "get_store", _must_not_run):
            assert cached(seam, key_input, lambda: result, _identity, _identity) == result
        assert not path.exists() and not path.parent.exists()


def test_replay_with_no_cassette_file_is_empty_and_goes_live(tmp_path) -> None:
    with demo("replay", tmp_path / "missing.json"), captured_warnings() as warnings:
        assert cached("llm", {"p": 1}, lambda: "live", _identity, _identity) == "live"
    assert len(warnings) == 1 and not (tmp_path / "missing.json").exists()


def test_record_writes_on_first_entry_and_adds_model(tmp_path) -> None:
    path = tmp_path / "c.json"
    with demo("record", path):
        cached("llm", {"p": 1}, lambda: "r", _identity, _identity, label="L", model="m1")
    entry = json.loads(path.read_text())["entries"][request_key("llm", {"p": 1})]
    assert entry == {"seam": "llm", "label": "L", "model": "m1", "recorded": "r"}


# --- Property 9 ---------------------------------------------------------------


# Feature: demo-mode, Property 9: Secret values are never written
@settings(max_examples=100)
@given(secret_tail=_secret_text, clean=_json, where=st.sampled_from(["label", "recorded"]))
def test_secrets_are_never_written(secret_tail, clean, where) -> None:
    secret = "SECRET-" + secret_tail
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "c.json"
        store = CassetteStore(path)
        store.put("llm:ok", {"seam": "llm", "label": "fine", "recorded": 1})
        before = path.read_bytes()
        bad = {"seam": "llm", "label": "x", "recorded": ["a"]}
        bad[where] = secret if where == "label" else [{"nested": secret}]
        with mock.patch.dict(os.environ, {"AWS_SECRET_ACCESS_KEY": secret}):
            with pytest.raises(CassetteError):
                store.put("llm:bad", bad)
            assert path.read_bytes() == before
            assert store.get("llm:bad") is None
            store.put("llm:clean", {"seam": "llm", "label": "fine", "recorded": clean})
        assert CassetteStore(path).get("llm:clean")["recorded"] == clean


@pytest.mark.parametrize("field", ["github_token", "session_secret"])
def test_settings_secrets_are_also_guarded(tmp_path, field) -> None:
    s = get_settings().model_copy(update={field: "tok-123456"})
    with mock.patch.object(cassette, "get_settings", lambda: s):
        with pytest.raises(CassetteError):
            entry = {"seam": "llm", "label": "tok-123456", "recorded": 1}
            CassetteStore(tmp_path / "c.json").put("k", entry)


# --- Property 10 --------------------------------------------------------------

_VALID_BUT_UNSUPPORTED = [
    b"[]",
    b'{"version": 2, "entries": {}}',
    b'{"entries": {}}',
    b'{"version": 1}',
    b'{"version": 1, "entries": []}',
    b"",
    b"\xff\xfe\x00",
]


# Feature: demo-mode, Property 10: Corrupt or unsupported Cassettes are rejected and preserved
@settings(max_examples=100)
@given(content=st.one_of(st.binary(), st.sampled_from(_VALID_BUT_UNSUPPORTED)))
def test_corrupt_cassette_is_rejected_and_preserved(content) -> None:
    try:
        doc = json.loads(content.decode("utf-8"))
        entries = doc.get("entries") if isinstance(doc, dict) else None
        if isinstance(doc, dict) and doc.get("version") == 1 and isinstance(entries, dict):
            return  # a valid cassette: not this property's concern
    except ValueError:
        pass
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "c.json"
        path.write_bytes(content)
        store = CassetteStore(path)
        with pytest.raises(CassetteError) as exc:
            store.get("llm:x")
        assert str(path) in str(exc.value)
        with pytest.raises(CassetteError):
            store.put("llm:x", {"seam": "llm", "label": "", "recorded": 1})
        assert path.read_bytes() == content

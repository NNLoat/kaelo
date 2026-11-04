"""Seam wrappers for demo-mode (spec demo-mode, task 4).

Codec properties plus wiring tests for the LLM, source and repo seams. No network,
Bedrock or GitHub: every real boundary is replaced by a local fake, and a fake that
must not run raises.
"""

import inspect
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from unittest import mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.core import codegen
from app.models.paper import PaperDomain
from app.services import llm, scoring
from app.services.demo import cassette, seams
from app.services.repro import explainer, extractor, inspector
from app.services.repro.types import RepoSignals
from app.services.sources.base import SourceRecord
from tests.demo_helpers import demo

_text_or_none = st.none() | st.text()
_records = st.builds(
    SourceRecord,
    source=st.sampled_from(["openalex", "arxiv"]),
    title=st.text(),
    authors=st.lists(st.text(), max_size=3),
    abstract=_text_or_none,
    published_date=st.none() | st.dates(),
    doi=_text_or_none,
    arxiv_id=_text_or_none,
    source_links=st.lists(st.tuples(st.text(), st.text()), max_size=3),
    repo_url=_text_or_none,
    domain=st.sampled_from(list(PaperDomain)),
)
_signals = st.builds(
    RepoSignals,
    exists=st.booleans(),
    has_readme=st.booleans(),
    has_license=st.booleans(),
    has_tests=st.booleans(),
    recent_activity=st.booleans(),
    inspectable=st.booleans(),
    failed=st.booleans(),
)


class _Resp:
    def __init__(self, content):
        self.content = content


class _Chat:
    def __init__(self, text):
        self._text = text

    def invoke(self, _prompt):
        return _Resp(self._text)


def _boom(*_a, **_k):
    raise AssertionError("must not run")


# --- Property 8 ---------------------------------------------------------------


# Feature: demo-mode, Property 8: Codecs round-trip
@settings(max_examples=100)
@given(records=st.lists(_records, max_size=5))
def test_source_records_round_trip_through_json(records) -> None:
    wire = json.loads(json.dumps(seams._encode_records(records)))
    decoded = seams._decode_records(wire)
    assert decoded == records
    for r in decoded:  # equality alone would pass for a str: code uses `is PaperDomain.x`
        assert type(r.domain) is PaperDomain
        assert r.published_date is None or type(r.published_date) is date
        assert all(type(link) is tuple for link in r.source_links)


# Feature: demo-mode, Property 8: Codecs round-trip
@settings(max_examples=100)
@given(signals=_signals)
def test_repo_signals_round_trip_through_json(signals) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "c.json"
        with demo("record", path):
            seams.cached_repo("https://github.com/o/r", lambda: signals)
        with demo("replay", path):
            assert seams.cached_repo("https://github.com/o/r", _boom) == signals


# Feature: demo-mode, Property 8: Codecs round-trip
@settings(max_examples=100)
@given(text=st.text())
def test_llm_text_round_trips(text) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "c.json"
        with demo("record", path):
            assert seams.wrap_chat(lambda: _Chat(text)).invoke("p").content == text
        with demo("replay", path):
            assert seams.wrap_chat(_boom).invoke("p").content == text


# --- Off is transparent -------------------------------------------------------


def test_off_returns_the_real_client_and_adapter(tmp_path) -> None:
    sentinel, adapter = object(), mock.Mock(spec=["name", "fetch"])
    with demo("off", tmp_path / "c.json"):
        assert seams.wrap_chat(lambda: sentinel) is sentinel
        assert seams.wrap_source(adapter) is adapter


# --- LLM seam wiring ----------------------------------------------------------


def _clear_llm_cache():
    llm._client.cache_clear()


@pytest.mark.parametrize("module", [llm, extractor, explainer], ids=lambda m: m.__name__)
def test_client_builds_bedrock_lazily_except_when_off(module, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(module, "ChatBedrock", _boom)
    _clear_llm_cache()
    with demo("replay", tmp_path / "c.json"):
        assert isinstance(module._client(), seams.CassetteChat)  # nothing constructed
    _clear_llm_cache()
    with demo("off", tmp_path / "c.json"), pytest.raises(AssertionError):
        module._client()  # off builds the real client eagerly, as before
    _clear_llm_cache()


def test_expand_query_records_then_replays_without_credentials(tmp_path, monkeypatch) -> None:
    path = tmp_path / "c.json"
    monkeypatch.setattr(llm, "ChatBedrock", lambda **_: _Chat("deep learning, neural nets"))
    _clear_llm_cache()
    with demo("record", path):
        assert llm.expand_query("deep learning") == "deep learning, neural nets"
    entry = next(iter(json.loads(path.read_text())["entries"].values()))
    assert entry["seam"] == "llm" and entry["model"] and entry["label"].startswith("Rewrite")

    monkeypatch.setattr(llm, "ChatBedrock", _boom)
    _clear_llm_cache()
    no_creds = {"AWS_ACCESS_KEY_ID": "", "AWS_SECRET_ACCESS_KEY": ""}
    with demo("replay", path), mock.patch.dict(os.environ, no_creds):
        assert llm.expand_query("deep learning") == "deep learning, neural nets"
    _clear_llm_cache()


def test_extract_setup_replays(tmp_path, monkeypatch) -> None:
    path = tmp_path / "c.json"
    reply = '{"hyperparameters": "lr=1e-3", "datasets": null, "environment": "python 3.13"}'
    monkeypatch.setattr(extractor, "ChatBedrock", lambda **_: _Chat(reply))
    with demo("record", path):
        live = extractor.extract_setup("T", "A")
    monkeypatch.setattr(extractor, "ChatBedrock", _boom)
    with demo("replay", path):
        assert extractor.extract_setup("T", "A") == live
    assert live.hyperparameters == "lr=1e-3" and live.datasets is None


# --- Source seam wiring -------------------------------------------------------


class _Adapter:
    name = "openalex"

    def __init__(self, records):
        self._records = records

    def fetch(self, query, *, limit, timeout):
        return self._records


def test_adapters_are_wrapped_in_record_and_replay_only(tmp_path, monkeypatch) -> None:
    records = [
        SourceRecord(source="openalex", title="T", doi="10.1/x", domain=PaperDomain.medicine)
    ]
    live = _Adapter(records)
    monkeypatch.setattr(scoring, "_ADAPTERS", [live])
    path = tmp_path / "c.json"

    with demo("off", path):
        assert scoring._adapters() == [live]
    with demo("record", path):
        (wrapped,) = scoring._adapters()
        assert wrapped.name == "openalex"
        assert wrapped.fetch("q", limit=25, timeout=1.0) == records

    monkeypatch.setattr(scoring, "_ADAPTERS", [_Adapter(None)])  # a live call would fail
    monkeypatch.setattr(_Adapter, "fetch", _boom)
    with demo("replay", path):
        (wrapped,) = scoring._adapters()
        assert wrapped.fetch("q", limit=25, timeout=1.0) == records


def test_source_key_includes_query_and_limit(tmp_path) -> None:
    path = tmp_path / "c.json"
    with demo("record", path):
        wrapped = seams.wrap_source(_Adapter([]))
        wrapped.fetch("a", limit=25, timeout=1.0)
        wrapped.fetch("b", limit=25, timeout=1.0)
        wrapped.fetch("a", limit=10, timeout=1.0)
    assert len(json.loads(path.read_text())["entries"]) == 3


# --- Repo seam wiring ---------------------------------------------------------

_GOOD = RepoSignals(True, True, True, True, True, True, False)


class _Host:
    def __init__(self, signals):
        self._signals = signals

    def inspect(self, repo_url, *, timeout):
        return self._signals


def test_inspect_repo_records_then_replays(tmp_path, monkeypatch) -> None:
    path = tmp_path / "c.json"
    monkeypatch.setattr(inspector, "_HOST", _Host(_GOOD))
    with demo("record", path):
        assert inspector.inspect_repo("https://github.com/o/r") == _GOOD
    monkeypatch.setattr(inspector, "_HOST", mock.Mock(inspect=_boom))
    with demo("replay", path):
        assert inspector.inspect_repo("https://github.com/o/r") == _GOOD
        assert inspector.inspect_repo(" https://github.com/o/r ") == _GOOD  # url is stripped


@pytest.mark.parametrize("mode", ["off", "record", "replay"])
@pytest.mark.parametrize("url", [None, "", "   "])
def test_no_repo_url_does_no_lookup(mode, url, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(inspector, "_HOST", mock.Mock(inspect=_boom))
    with demo(mode, tmp_path / "c.json"), mock.patch.object(cassette, "get_store", _boom):
        sig = inspector.inspect_repo(url)
    assert sig.inspectable is False and sig.failed is False
    assert not (tmp_path / "c.json").exists()


# --- Code generation is not recorded -----------------------------------------


def test_codegen_is_never_recorded(tmp_path, monkeypatch) -> None:
    assert "wrap_chat" not in inspect.getsource(codegen)
    monkeypatch.setattr(codegen, "_client", lambda: _Chat('{"score": 0.7, "rationale": "ok"}'))
    path = tmp_path / "c.json"
    for mode in ("record", "replay"):
        with demo(mode, path):
            assert codegen.score([codegen.GenFile(path="a.py", content="x = 1")]).score == 0.7
    assert not path.exists()

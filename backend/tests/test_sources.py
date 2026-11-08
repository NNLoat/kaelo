"""Adapter mapping/scope/failure and LLM failure-handling tests.

External Sources and the LLM are mocked — never called for real.
"""

import httpx
import pytest

from app.services import llm
from app.services.llm import PaperSummary
from app.services.sources.arxiv import ArxivAdapter
from app.services.sources.base import SourceError, find_repo_url
from app.services.sources.openalex import OpenAlexAdapter

_OPENALEX_SAMPLE = {
    "results": [
        {
            "display_name": "A Study of Reproducibility",
            "doi": "https://doi.org/10.1/abc",
            "publication_date": "2024-05-01",
            "authors": [],
            "authorships": [{"author": {"display_name": "Ada Lovelace"}}],
            "abstract_inverted_index": {"Hello": [0], "world": [1]},
            "primary_location": {"landing_page_url": "https://example.org/paper"},
            "open_access": {"oa_url": None},
        }
    ]
}

_ARXIV_SAMPLE = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.00001v2</id>
    <title>Deep Learning for Science</title>
    <summary>An abstract.</summary>
    <published>2024-01-02T00:00:00Z</published>
    <author><name>Grace Hopper</name></author>
  </entry>
</feed>"""


def test_openalex_maps_record(monkeypatch) -> None:
    def fake_get(url, params=None, timeout=None):
        return httpx.Response(200, json=_OPENALEX_SAMPLE, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    [rec] = OpenAlexAdapter().fetch("repro", limit=5, timeout=1.0)
    assert rec.source == "openalex"
    assert rec.title == "A Study of Reproducibility"
    assert rec.doi == "10.1/abc"
    assert rec.authors == ["Ada Lovelace"]
    assert rec.abstract == "Hello world"
    assert ("openalex", "https://example.org/paper") in rec.source_links


def test_openalex_applies_domain_scope(monkeypatch) -> None:
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured["params"] = params
        return httpx.Response(200, json={"results": []}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    OpenAlexAdapter().fetch("q", limit=5, timeout=1.0)
    assert "fields/17" in captured["params"]["filter"]
    assert "fields/27" in captured["params"]["filter"]


def test_openalex_raises_source_error_on_failure(monkeypatch) -> None:
    def fake_get(url, params=None, timeout=None):
        raise httpx.TimeoutException("boom")

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(SourceError):
        OpenAlexAdapter().fetch("q", limit=5, timeout=0.01)


def test_arxiv_maps_record_and_scope(monkeypatch) -> None:
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured["params"] = params
        return httpx.Response(200, text=_ARXIV_SAMPLE, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    [rec] = ArxivAdapter().fetch("dl", limit=5, timeout=1.0)
    assert rec.source == "arxiv"
    assert rec.title == "Deep Learning for Science"
    assert rec.arxiv_id == "2401.00001v2"
    assert rec.authors == ["Grace Hopper"]
    assert "cat:cs." in captured["params"]["search_query"]


def test_arxiv_raises_source_error_on_failure(monkeypatch) -> None:
    def fake_get(url, params=None, timeout=None):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(SourceError):
        ArxivAdapter().fetch("q", limit=5, timeout=0.01)


class _FakeResp:
    def __init__(self, content):
        self.content = content


def test_expand_query_falls_back_on_llm_error(monkeypatch) -> None:
    # The caller falls back to raw; here we assert the raw survives the pipeline
    # path by having the client raise and verifying run_search behavior elsewhere.
    # Direct check: expand_query propagates, caller catches (see scoring tests).
    class Boom:
        def invoke(self, _):
            raise RuntimeError("llm down")

    monkeypatch.setattr(llm, "_client", lambda: Boom())
    with pytest.raises(RuntimeError):
        llm.expand_query("raw")


def test_assess_relevance_raises_on_llm_error(monkeypatch) -> None:
    class Boom:
        def invoke(self, _):
            raise RuntimeError("llm down")

    monkeypatch.setattr(llm, "_client", lambda: Boom())
    with pytest.raises(RuntimeError):
        llm.assess_relevance(PaperSummary(title="t", abstract=None), "q")


def test_assess_relevance_parses_json(monkeypatch) -> None:
    monkeypatch.setattr(llm, "_client", lambda: _Client('{"score": 0.9, "blurb": "relevant"}'))
    result = llm.assess_relevance(PaperSummary(title="t", abstract="a"), "q")
    assert result.score == 0.9
    assert result.blurb == "relevant"


class _Client:
    def __init__(self, text):
        self._text = text

    def invoke(self, _):
        return _FakeResp(self._text)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Code: https://github.com/frankkramer-lab/MIScnn.", "https://github.com/frankkramer-lab/MIScnn"),
        ("see (github.com/a/b.git), and github.com/c/d", "https://github.com/a/b"),
        ("no link here", None),
        (None, None),
    ],
)
def test_find_repo_url(text, expected) -> None:
    assert find_repo_url(text) == expected

"""Example/edge tests for the Search_API endpoints.

Driven through TestClient against the testcontainer DB with faked adapters and a
mocked LLM — external Sources and the LLM are never called for real.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.services import scoring
from app.services.llm import RelevanceResult
from app.services.sources.base import SourceError, SourceRecord


class FakeAdapter:
    def __init__(self, name, records=None, fail=False):
        self.name = name
        self._records = records or []
        self._fail = fail

    def fetch(self, query, *, limit, timeout):
        if self._fail:
            raise SourceError(f"{self.name} failed")
        return self._records


def _rec(source, doi, title):
    return SourceRecord(source=source, title=title, authors=["A"], doi=doi)


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch, engine):
    """Expand is identity; relevance is deterministic. Never calls Bedrock.

    Background scoring opens its own Session; point it at the test engine so it
    can't reach the (unreachable-from-host) production ``db`` host. Under the
    rollback fixture the row isn't committed, so the job no-ops harmlessly.
    """
    monkeypatch.setattr(scoring, "engine", engine)
    monkeypatch.setattr(scoring, "expand_query", lambda raw: raw)
    monkeypatch.setattr(
        scoring,
        "assess_relevance",
        lambda paper, query: RelevanceResult(score=0.8, blurb="relevant"),
    )


def _set_adapters(monkeypatch, adapters):
    monkeypatch.setattr(scoring, "_ADAPTERS", adapters)


@pytest.mark.parametrize("bad", ["", "   ", "x" * 513])
def test_invalid_query_returns_422(client: TestClient, bad: str) -> None:
    resp = client.post("/api/papers/search", json={"query": bad})
    assert resp.status_code == 422


def test_all_sources_fail_returns_502(client: TestClient, monkeypatch) -> None:
    _set_adapters(
        monkeypatch,
        [FakeAdapter("openalex", fail=True), FakeAdapter("arxiv", fail=True)],
    )
    resp = client.post("/api/papers/search", json={"query": "deep learning"})
    assert resp.status_code == 502
    assert resp.json()["detail"]["source_failure"] is True


def test_zero_records_is_200_empty(client: TestClient, monkeypatch) -> None:
    _set_adapters(monkeypatch, [FakeAdapter("openalex", []), FakeAdapter("arxiv", [])])
    resp = client.post("/api/papers/search", json={"query": "deep learning"})
    assert resp.status_code == 200
    assert resp.json()["papers"] == []
    assert resp.json()["failed_sources"] == []


def test_partial_failure_lists_failed_source(client: TestClient, monkeypatch) -> None:
    _set_adapters(
        monkeypatch,
        [
            FakeAdapter("openalex", [_rec("openalex", "10.1/a", "Paper A")]),
            FakeAdapter("arxiv", fail=True),
        ],
    )
    resp = client.post("/api/papers/search", json={"query": "deep learning"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["failed_sources"] == ["arxiv"]
    assert len(body["papers"]) == 1
    assert body["papers"][0]["title"] == "Paper A"


def test_end_to_end_search_and_detail(client: TestClient, monkeypatch) -> None:
    _set_adapters(
        monkeypatch,
        [FakeAdapter("openalex", [_rec("openalex", "10.1/e2e", "End To End")])],
    )
    # Search returns the card with (initially) pending scores.
    search = client.post("/api/papers/search", json={"query": "repro"})
    assert search.status_code == 200
    pid = search.json()["papers"][0]["id"]

    # Scores endpoint returns the paper's current component cells.
    scores = client.get(f"/api/papers/scores?ids={pid}")
    assert scores.status_code == 200
    assert str(pid) in scores.json()

    detail = client.get(f"/api/papers/{pid}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "End To End"


def test_detail_404_for_unknown(client: TestClient) -> None:
    resp = client.get("/api/papers/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "paper not found"


@pytest.mark.parametrize("enabled", [True, False])
def test_query_expansion_flag(client: TestClient, monkeypatch, enabled: bool) -> None:
    seen: list[str] = []
    adapter = FakeAdapter("openalex", [])
    adapter_fetch = adapter.fetch

    def spy_fetch(query, **kw):
        seen.append(query)
        return adapter_fetch(query, **kw)

    monkeypatch.setattr(adapter, "fetch", spy_fetch)
    monkeypatch.setattr(scoring, "expand_query", lambda raw: raw + " EXPANDED")
    monkeypatch.setattr(
        scoring,
        "get_settings",
        lambda: get_settings().model_copy(update={"query_expansion_enabled": enabled}),
    )
    _set_adapters(monkeypatch, [adapter])
    assert client.post("/api/papers/search", json={"query": "q"}).status_code == 200
    assert seen == ["q EXPANDED" if enabled else "q"]

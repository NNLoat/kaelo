"""Property-based tests for Search_API behavior (Hypothesis, >=100).

Faked adapters and a mocked LLM — external Sources and Bedrock are never called.
Score-lifecycle properties drive the orchestrator directly against a committed
row (background jobs open their own Session, so they need committed state).
"""

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import Engine
from sqlmodel import Session, select

from app.models.paper import Paper, ScoreStatus
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


def _rec(source, doi, title="Paper"):
    return SourceRecord(source=source, title=title, authors=["A"], doi=doi)


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch, engine):
    monkeypatch.setattr(scoring, "engine", engine)
    monkeypatch.setattr(scoring, "expand_query", lambda raw: raw)
    monkeypatch.setattr(
        scoring,
        "assess_relevance",
        lambda paper, query: RelevanceResult(score=0.8, blurb="relevant"),
    )


# Property 6: One source failing never fails the search.
# Validates: Requirements 4.6, 4.7, 7.5
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(oa_ok=st.booleans(), ax_ok=st.booleans())
def test_one_source_failing_never_fails_search(client: TestClient, monkeypatch, oa_ok, ax_ok):
    oa = FakeAdapter("openalex", [_rec("openalex", "10.1/oa")] if oa_ok else None, fail=not oa_ok)
    ax = FakeAdapter("arxiv", [_rec("arxiv", "10.2/ax")] if ax_ok else None, fail=not ax_ok)
    monkeypatch.setattr(scoring, "_ADAPTERS", [oa, ax])

    resp = client.post("/api/papers/search", json={"query": "q"})
    if not oa_ok and not ax_ok:
        assert resp.status_code == 502
        assert resp.json()["detail"]["source_failure"] is True
    else:
        assert resp.status_code == 200
        failed = set(resp.json()["failed_sources"])
        assert ("openalex" in failed) == (not oa_ok)
        assert ("arxiv" in failed) == (not ax_ok)


# Property 7: Query validation rejects before any fetch.
# Validates: Requirements 1.1, 4.5
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    bad=st.one_of(
        st.just(""),
        st.text(alphabet=" \t\n", max_size=5),
        st.text(min_size=513, max_size=600),
    )
)
def test_validation_rejects_before_fetch(client: TestClient, monkeypatch, bad):
    called = {"n": 0}

    class Spy(FakeAdapter):
        def fetch(self, *a, **k):
            called["n"] += 1
            return []

    monkeypatch.setattr(scoring, "_ADAPTERS", [Spy("openalex"), Spy("arxiv")])
    monkeypatch.setattr(
        scoring, "expand_query", lambda raw: (_ for _ in ()).throw(AssertionError("called"))
    )

    resp = client.post("/api/papers/search", json={"query": bad})
    assert resp.status_code == 422
    assert called["n"] == 0


# Property 8: Caching persists Papers but never the query.
# Validates: Requirements 4.2, 9.1
def test_caching_persists_papers_not_query(client: TestClient, monkeypatch, session: Session):
    monkeypatch.setattr(
        scoring, "_ADAPTERS", [FakeAdapter("openalex", [_rec("openalex", "10.1/c", "Cached")])]
    )
    resp = client.post("/api/papers/search", json={"query": "secret-query-text"})
    assert resp.status_code == 200
    rows = session.exec(select(Paper)).all()
    assert any(p.title == "Cached" for p in rows)
    # No table holds the query text; only the Paper table exists for this feature.
    for p in rows:
        assert "secret-query-text" not in (p.title + (p.abstract or ""))


# Property 9: Re-search reuses cached Papers rather than duplicating.
# Validates: Requirements 9.4, 9.5
def test_research_reuses_cached_paper(client: TestClient, monkeypatch, session: Session):
    monkeypatch.setattr(
        scoring, "_ADAPTERS", [FakeAdapter("openalex", [_rec("openalex", "10.1/dup", "Dup")])]
    )
    first = client.post("/api/papers/search", json={"query": "q"}).json()["papers"][0]["id"]
    second = client.post("/api/papers/search", json={"query": "q again"}).json()["papers"][0]["id"]
    assert first == second
    rows = session.exec(select(Paper).where(Paper.doi == "10.1/dup")).all()
    assert len(rows) == 1


# Property 12: Detail is served from cache and 404s for unknown ids.
# Validates: Requirements 6.1, 6.2, 6.5
def test_detail_from_cache_and_404(client: TestClient, monkeypatch):
    spy = FakeAdapter("openalex", [_rec("openalex", "10.1/d", "Detail")])
    monkeypatch.setattr(scoring, "_ADAPTERS", [spy])
    pid = client.post("/api/papers/search", json={"query": "q"}).json()["papers"][0]["id"]

    # Detail must not re-fetch: break the adapter, then read detail.
    spy._fail = True
    detail = client.get(f"/api/papers/{pid}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Detail"
    assert client.get("/api/papers/88888").status_code == 404


# --- Score-lifecycle properties: drive the orchestrator against committed rows ---


def _committed_paper(engine: Engine) -> int:
    with Session(engine) as s:
        p = Paper(title="Scoring", authors=["A"], doi="10.9/score", sources=["openalex"])
        s.add(p)
        s.commit()
        s.refresh(p)
        return p.id


def _cleanup(engine: Engine, pid: int) -> None:
    with Session(engine) as s:
        obj = s.get(Paper, pid)
        if obj:
            s.delete(obj)
            s.commit()


# Property 10: Score lifecycle terminates — no component stays pending.
# Validates: Requirements 5.3, 5.4, 8.4
@pytest.mark.parametrize("llm_fails", [False, True])
def test_score_lifecycle_terminates(engine: Engine, monkeypatch, llm_fails):
    if llm_fails:

        def boom(paper, query):
            raise RuntimeError("llm down")

        monkeypatch.setattr(scoring, "assess_relevance", boom)
    else:
        monkeypatch.setattr(
            scoring,
            "assess_relevance",
            lambda paper, query: RelevanceResult(score=0.8, blurb="b"),
        )

    pid = _committed_paper(engine)
    monkeypatch.setattr(scoring, "engine", engine)
    try:
        scoring.run_scoring_for_paper(pid, "q")
        with Session(engine) as s:
            p = s.get(Paper, pid)
            assert p.relevance_status in (ScoreStatus.ready, ScoreStatus.unavailable)
            assert p.reproducibility_status in (ScoreStatus.ready, ScoreStatus.unavailable)
            assert p.final_status in (ScoreStatus.ready, ScoreStatus.unavailable)
            if llm_fails:
                assert p.relevance_status == ScoreStatus.unavailable
                assert p.relevance_score is None  # never fabricated
    finally:
        _cleanup(engine, pid)


# Property 11: The reproducibility stub produces a full score lifecycle.
# Validates: Requirements 5.6
def test_reproducibility_stub_full_lifecycle(engine: Engine, monkeypatch):
    monkeypatch.setattr(
        scoring,
        "assess_relevance",
        lambda paper, query: RelevanceResult(score=0.5, blurb="b"),
    )
    pid = _committed_paper(engine)
    monkeypatch.setattr(scoring, "engine", engine)
    try:
        scoring.run_scoring_for_paper(pid, "q")
        with Session(engine) as s:
            p = s.get(Paper, pid)
            assert p.reproducibility_status == ScoreStatus.ready
            assert p.reproducibility_score is not None
            assert p.final_status == ScoreStatus.ready
            assert p.final_score is not None
    finally:
        _cleanup(engine, pid)

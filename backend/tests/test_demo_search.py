"""Search_API in demo record/replay (spec demo-mode, task 6).

The real endpoint, scoring and ranking run against the test database; only the
outside world (sources, Bedrock, GitHub) is faked. Scoring opens its own sessions,
so these tests use committed rows and truncate between runs.
"""

import re
import tempfile
from collections import Counter
from pathlib import Path
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import text
from sqlmodel import Session, select

from app.db.session import get_session
from app.main import app
from app.models.paper import Paper, PaperDomain, ScoreStatus
from app.models.reproducibility import ExperimentSetup, ReproducibilityScore
from app.routers import papers as papers_router
from app.services import llm, scoring
from app.services import reproducibility as seam
from app.services.demo import cassette, seams
from app.services.repro import explainer, extractor, inspector
from app.services.repro.types import RepoSignals
from app.services.sources.base import SourceRecord
from tests.demo_helpers import demo

_TABLES = ", ".join(
    m.__tablename__ for m in (Paper, ReproducibilityScore, ExperimentSetup)
)  # CASCADE below covers FKs between them
_STALE = 0.9876  # a value no run can produce (specs round to 2 decimals)


def _n(prompt: str, pattern: str) -> int:
    return int(re.search(pattern, prompt).group(1))


class World:
    """Fake outside world driven by ``specs`` (one dict per paper)."""

    name = "openalex"

    def __init__(self, engine, monkeypatch):
        self.engine = engine
        self.specs: list[dict] = []
        self.live_allowed = True
        self.calls: Counter = Counter()
        monkeypatch.setattr(scoring, "_ADAPTERS", [self])
        monkeypatch.setattr(scoring, "engine", engine)
        monkeypatch.setattr(seam, "engine", engine)
        monkeypatch.setattr(inspector, "_HOST", self)
        for module in (llm, extractor, explainer):
            monkeypatch.setattr(module, "_client", lambda: seams.wrap_chat(lambda: self))

    def _live(self, what: str) -> None:
        self.calls[what] += 1
        if not self.live_allowed:
            raise AssertionError(f"live {what} call during replay")

    # source adapter
    def fetch(self, query, *, limit, timeout):
        self._live("source")
        return [
            SourceRecord(
                source="openalex",
                title=f"Paper {i}",
                authors=["A"],
                abstract=f"abstract {i}",
                doi=f"10.1/{i}",
                repo_url=f"https://github.com/o/r{i}" if s["repo"] else None,
                domain=PaperDomain.computer_science,
            )
            for i, s in enumerate(self.specs)
        ]

    # chat client
    def invoke(self, prompt):
        self._live("llm")
        if "Rewrite this scientific-paper" in prompt:
            return _Resp("rewritten query")
        if "Rate how relevant" in prompt:
            spec = self.specs[_n(prompt, r"Title: Paper (\d+)")]
            if spec["rel_fail"]:
                raise RuntimeError("relevance LLM down")
            return _Resp(f'{{"score": {spec["rel"]}, "blurb": "blurb"}}')
        if "Extract the experiment setup" in prompt:
            if self.specs[_n(prompt, r"Title: Paper (\d+)")]["setup_fail"]:
                raise RuntimeError("setup LLM down")
            return _Resp('{"hyperparameters": "lr=1e-3", "datasets": "d", "environment": "py"}')
        return _Resp("an explanation")

    # repo host
    def inspect(self, repo_url, *, timeout):
        self._live("repo")
        n = int(repo_url.rsplit("r", 1)[1])
        return RepoSignals(True, True, n % 2 == 0, n % 3 == 0, n % 2 == 1, True, False)

    # DB + HTTP
    def reset(self, restart: bool = True) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(f"TRUNCATE {_TABLES} {'RESTART IDENTITY ' if restart else ''}CASCADE")
            )

    def seed_stale(self) -> None:
        """Paper 0 already exists from an 'earlier search' with scores no run produces."""
        with Session(self.engine) as s:
            s.add(
                Paper(
                    title="Paper 0",
                    authors=["A"],
                    sources=["openalex"],
                    source_links=[],
                    doi="10.1/0",
                    domain=PaperDomain.computer_science,
                    relevance_score=_STALE,
                    relevance_status=ScoreStatus.ready,
                    reproducibility_score=_STALE,
                    reproducibility_status=ScoreStatus.ready,
                    final_score=_STALE,
                    final_status=ScoreStatus.ready,
                )
            )
            s.commit()

    def search(self, query: str = "q") -> dict:
        def committed_session():
            with Session(self.engine) as s:
                yield s

        app.dependency_overrides[get_session] = committed_session
        try:
            with TestClient(app) as client:
                resp = client.post("/api/papers/search", json={"query": query})
        finally:
            app.dependency_overrides.clear()
        assert resp.status_code == 200, resp.text
        return resp.json()


class _Resp:
    def __init__(self, content):
        self.content = content


@pytest.fixture
def world(engine, monkeypatch):
    w = World(engine, monkeypatch)
    w.reset()
    yield w
    w.reset()


def _demo(mode, path):
    return demo(mode, path, also=[papers_router])


def _cells(card):
    return (card["relevance"], card["reproducibility"], card["final"])


_spec = st.fixed_dictionaries(
    {
        "rel": st.floats(0.0, 1.0).map(lambda x: round(x, 2)),
        "repo": st.booleans(),
        "rel_fail": st.booleans(),
        "setup_fail": st.booleans(),
    }
)
_ok_spec = st.fixed_dictionaries(
    {
        "rel": st.floats(0.0, 1.0).map(lambda x: round(x, 2)),
        "repo": st.booleans(),
        "rel_fail": st.just(False),
        "setup_fail": st.just(False),
    }
)
_slow = dict(
    max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)


# Feature: demo-mode, Property 12: Inline scoring leaves no pending cell and no stale value
@settings(**_slow)
@given(
    specs=st.lists(_spec, min_size=1, max_size=5),
    mode=st.sampled_from(["record", "replay"]),
)
def test_inline_scoring_is_terminal_fresh_and_sorted(world, specs, mode) -> None:
    world.reset()
    world.specs = specs
    world.seed_stale()
    with tempfile.TemporaryDirectory() as tmp, _demo(mode, Path(tmp) / "c.json"):
        body = world.search()

    cards = body["papers"]
    assert len(cards) == len(specs)
    for card in cards:
        assert all(c["status"] in ("ready", "unavailable") for c in _cells(card))
        assert all(c["value"] != _STALE for c in _cells(card))
    by_title = {c["title"]: c for c in cards}
    first = by_title["Paper 0"]
    if specs[0]["rel_fail"]:
        assert first["relevance"] == {"status": "unavailable", "value": None}
        assert first["final"]["status"] == "unavailable"
    else:
        assert first["relevance"] == {"status": "ready", "value": specs[0]["rel"]}

    def key(c):
        ready = c["final"]["status"] == "ready"
        return (not ready, -c["final"]["value"] if ready else 0.0, c["id"])

    assert cards == sorted(cards, key=key)


# Feature: demo-mode, Property 13: Replay is repeatable end to end
@settings(**_slow)
@given(specs=st.lists(_ok_spec, min_size=1, max_size=5))
def test_replay_is_repeatable_end_to_end(world, specs) -> None:
    world.specs = specs
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "c.json"
        world.reset()
        with _demo("record", path):
            recorded = world.search()
        assert world.calls["llm"] > 0

        world.live_allowed = False
        world.calls.clear()
        runs = []
        with _demo("replay", path):
            runs.append(world.search())  # DB already holds the papers
            runs.append(world.search())
            world.reset()  # a fresh `demo-reset`: same ids come back
            runs.append(world.search())
        assert world.calls == Counter()  # nothing reached a live seam
        assert runs == [recorded] * 3
        world.live_allowed = True


def test_replay_miss_goes_live_and_leaves_the_cassette_unchanged(world, tmp_path) -> None:
    world.specs = [{"rel": 0.5, "repo": True, "rel_fail": False, "setup_fail": False}]
    path = tmp_path / "c.json"
    with _demo("record", path):
        world.search("q1")
    before = path.read_bytes()
    world.calls.clear()
    with _demo("replay", path):
        body = world.search("q2")  # never recorded
    # The rewrite and relevance prompts embed the raw query, so they miss and go live;
    # the source call is keyed on the (identical) rewritten query, so it still hits.
    assert world.calls["llm"] > 0 and world.calls["source"] == 0
    assert len(body["papers"]) == 1
    assert path.read_bytes() == before


def test_off_keeps_background_scoring_and_never_opens_the_cassette(world, tmp_path) -> None:
    world.specs = [{"rel": 0.5, "repo": True, "rel_fail": False, "setup_fail": False}] * 2
    path = tmp_path / "c.json"
    with _demo("off", path), mock.patch.object(cassette, "get_store", side_effect=AssertionError):
        body = world.search()
    assert all(c["status"] == "pending" for card in body["papers"] for c in _cells(card))
    assert not path.exists()
    with Session(world.engine) as s:  # the background job still ran after the response
        rows = s.exec(select(Paper)).all()
    assert len(rows) == 2
    assert all(p.final_status in (ScoreStatus.ready, ScoreStatus.unavailable) for p in rows)

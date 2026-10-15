"""Property tests for the seam — real seam, faked inspector + mocked LLM.

The seam opens its own ``Session(engine)``; these tests point it at the test
engine and manage rows directly.
"""

import inspect as pyinspect

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlmodel import Session, delete, select

from app.core.config import get_settings
from app.models.paper import Paper, ScoreStatus
from app.models.reproducibility import ExperimentSetup, ReproducibilityScore
from app.services import reproducibility as seam
from app.services import scoring
from app.services.repro.types import (
    ExperimentSetupData,
    RepoSignals,
    ReproducibilityUnavailable,
)

GOOD_SIGNALS = RepoSignals(True, True, True, True, True, True, False)
NOT_INSPECTABLE = RepoSignals(False, False, False, False, False, False, False)


@pytest.fixture
def db(engine):
    seam.engine = engine
    yield engine
    with Session(engine) as s:
        s.exec(delete(ReproducibilityScore))
        s.exec(delete(ExperimentSetup))
        s.exec(delete(Paper))
        s.commit()


def _make_paper(engine, repo_url=None) -> int:
    with Session(engine) as s:
        p = Paper(title="T", abstract="A", repo_url=repo_url)
        s.add(p)
        s.commit()
        return p.id


def _patch(
    monkeypatch, *, signals, setup, extract_raises=False, explain_raises=False, explanation="x"
):
    monkeypatch.setattr(seam.inspector, "inspect_repo", lambda url: signals)

    def fake_extract(title, abstract):
        if extract_raises:
            raise RuntimeError("down")
        return setup

    def fake_explain(score, sig, comp):
        if explain_raises:
            raise RuntimeError("down")
        return explanation

    monkeypatch.setattr(seam, "extract_setup", fake_extract)
    monkeypatch.setattr(seam, "explain", fake_explain)


# Property 6: No signals at all means no score, not a fabricated one.
# Validates: Requirements 4.4, 6.4
def test_no_signals_raises(db, monkeypatch):
    pid = _make_paper(db, repo_url=None)
    _patch(monkeypatch, signals=NOT_INSPECTABLE, setup=None, extract_raises=True)
    with pytest.raises(ReproducibilityUnavailable):
        seam.score_reproducibility(pid)
    with Session(db) as s:
        assert s.get(Paper, pid).reproducibility_score is None


# Property 7: The score number never comes from the LLM.
# Validates: Requirements 2.3, 4.5, 5.2, 6.7
@settings(
    max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@given(
    hp=st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=1),
    ds=st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=1),
    expl=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
)
def test_score_independent_of_llm_text(db, monkeypatch, hp, ds, expl):
    pid = _make_paper(db, repo_url="https://github.com/o/r")
    # Fixed field-population (both populated), varying only the text + explanation.
    setup = ExperimentSetupData(hp, ds, None)
    _patch(monkeypatch, signals=GOOD_SIGNALS, setup=setup, explanation=expl)
    score = seam.score_reproducibility(pid)
    # Same signals + same populated-field pattern -> identical score regardless
    # of the LLM text, because the standard judges structure, not prose.
    from app.services.repro.scorer import reproducibility
    from app.services.repro.standards import Evidence

    expected = reproducibility(
        "unknown",
        Evidence(
            repo=GOOD_SIGNALS,
            code_quality=1.0,
            setup=setup,
            setup_completeness=2 / 3,
        ),
    ).score
    assert score == pytest.approx(expected)


# Property 8: Extraction and explanation failures degrade gracefully.
# Validates: Requirements 3.3, 5.3
def test_extract_fail_marks_unavailable_but_scores_from_repo(db, monkeypatch):
    pid = _make_paper(db, repo_url="https://github.com/o/r")
    _patch(monkeypatch, signals=GOOD_SIGNALS, setup=None, extract_raises=True)
    score = seam.score_reproducibility(pid)
    assert score > 0.0
    with Session(db) as s:
        setup_row = s.exec(select(ExperimentSetup).where(ExperimentSetup.paper_id == pid)).first()
        assert setup_row.available is False


# Property 11: Recompute updates in place, never duplicates.
# Validates: Requirements 7.4
@settings(
    max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@given(runs=st.integers(min_value=1, max_value=4))
def test_recompute_single_row(db, monkeypatch, runs):
    pid = _make_paper(db, repo_url="https://github.com/o/r")
    _patch(monkeypatch, signals=GOOD_SIGNALS, setup=ExperimentSetupData("a", "b", "c"))
    for _ in range(runs):
        seam.score_reproducibility(pid)
    with Session(db) as s:
        assert (
            len(
                s.exec(
                    select(ReproducibilityScore).where(ReproducibilityScore.paper_id == pid)
                ).all()
            )
            == 1
        )
        assert (
            len(s.exec(select(ExperimentSetup).where(ExperimentSetup.paper_id == pid)).all()) == 1
        )
    # cleanup between hypothesis examples so the next run upserts cleanly
    with Session(db) as s:
        s.exec(delete(ReproducibilityScore))
        s.exec(delete(ExperimentSetup))
        s.exec(delete(Paper))
        s.commit()


# Property 12: The GitHub token never leaks.
# Validates: Requirements 1.6, 7.5
def test_token_never_leaks(db, monkeypatch, caplog):
    sentinel = "ghp_SENTINEL_SECRET_TOKEN_123"
    monkeypatch.setattr(get_settings(), "github_token", sentinel, raising=False)
    captured_prompts = []

    pid = _make_paper(db, repo_url="https://github.com/o/r")
    monkeypatch.setattr(seam.inspector, "inspect_repo", lambda url: GOOD_SIGNALS)
    monkeypatch.setattr(seam, "extract_setup", lambda t, a: ExperimentSetupData("a", None, None))

    def spy_explain(score, sig, comp):
        captured_prompts.append(f"{score}{sig}{comp}")
        return "no secret here"

    monkeypatch.setattr(seam, "explain", spy_explain)

    with caplog.at_level("DEBUG"):
        seam.score_reproducibility(pid)

    assert all(sentinel not in p for p in captured_prompts)
    assert sentinel not in caplog.text
    with Session(db) as s:
        row = s.exec(
            select(ReproducibilityScore).where(ReproducibilityScore.paper_id == pid)
        ).first()
        assert sentinel not in str(row.model_dump())
        assert sentinel not in str(s.get(Paper, pid).model_dump())


# Property 13: The seam preserves the paper-search contract.
# Validates: Requirements 6.1, 6.3, 6.5, 6.6
def test_seam_signature_and_contract(db, monkeypatch):
    sig = pyinspect.signature(seam.score_reproducibility)
    assert list(sig.parameters) == ["paper_id"]

    # Drive the orchestrator with the real seam + faked inspector/LLM; the Final
    # Score must recompute from a ready reproducibility value.
    pid = _make_paper(db, repo_url="https://github.com/o/r")
    _patch(monkeypatch, signals=GOOD_SIGNALS, setup=ExperimentSetupData("a", "b", "c"))
    monkeypatch.setattr(scoring, "engine", db)

    from app.services.llm import RelevanceResult

    monkeypatch.setattr(
        scoring, "assess_relevance", lambda paper, query: RelevanceResult(score=0.9, blurb="r")
    )
    scoring.run_scoring_for_paper(pid, "query")
    with Session(db) as s:
        paper = s.get(Paper, pid)
        assert paper.reproducibility_status == ScoreStatus.ready
        assert paper.final_status == ScoreStatus.ready
        assert paper.final_score is not None

"""Seam example/edge tests — real seam, faked inspector + mocked LLM.

The seam opens its own ``Session(engine)``, so these tests point the seam's
engine at the test container engine and manage paper rows directly (the
rollback ``session`` fixture can't see the seam's committed writes).
"""

import pytest
from sqlmodel import Session, delete, select

from app.models.paper import Paper, ScoreStatus
from app.models.reproducibility import ExperimentSetup, ReproducibilityScore
from app.services import reproducibility as seam
from app.services.repro.types import (
    ExperimentSetupData,
    RepoSignals,
    ReproducibilityUnavailable,
)

GOOD_SIGNALS = RepoSignals(True, True, True, True, True, True, False)
NOT_INSPECTABLE = RepoSignals(False, False, False, False, False, False, False)
FULL_SETUP = ExperimentSetupData("lr=0.1", "ImageNet", "python 3.13")


@pytest.fixture
def db(engine):
    """Point the seam + its deps at the test engine; clean repro rows after."""
    seam.engine = engine
    yield engine
    with Session(engine) as s:
        s.exec(delete(ReproducibilityScore))
        s.exec(delete(ExperimentSetup))
        s.exec(delete(Paper))
        s.commit()


def _make_paper(engine, repo_url=None, title="T", abstract="A") -> int:
    with Session(engine) as s:
        p = Paper(title=title, abstract=abstract, repo_url=repo_url)
        s.add(p)
        s.commit()
        return p.id


def _patch(monkeypatch, *, signals, setup=FULL_SETUP, extract_raises=False, explain_raises=False):
    monkeypatch.setattr(seam.inspector, "inspect_repo", lambda url: signals)

    def fake_extract(title, abstract):
        if extract_raises:
            raise RuntimeError("llm down")
        return setup

    def fake_explain(score, sig, comp):
        if explain_raises:
            raise RuntimeError("llm down")
        return "because reasons"

    monkeypatch.setattr(seam, "extract_setup", fake_extract)
    monkeypatch.setattr(seam, "explain", fake_explain)


def test_no_repo_and_extract_fails_raises(db, monkeypatch):
    pid = _make_paper(db, repo_url=None)
    _patch(monkeypatch, signals=NOT_INSPECTABLE, extract_raises=True)
    with pytest.raises(ReproducibilityUnavailable):
        seam.score_reproducibility(pid)


def test_no_repo_but_setup_gives_real_score(db, monkeypatch):
    pid = _make_paper(db, repo_url=None)
    _patch(monkeypatch, signals=NOT_INSPECTABLE, setup=FULL_SETUP)
    score = seam.score_reproducibility(pid)
    assert score > 0.0
    with Session(db) as s:
        paper = s.get(Paper, pid)
        assert paper.reproducibility_status == ScoreStatus.ready
        assert paper.experiment_setup["available"] is True


def test_explainer_failure_persists_without_explanation(db, monkeypatch):
    pid = _make_paper(db, repo_url="https://github.com/o/r")
    _patch(monkeypatch, signals=GOOD_SIGNALS, explain_raises=True)
    seam.score_reproducibility(pid)
    with Session(db) as s:
        row = s.exec(
            select(ReproducibilityScore).where(ReproducibilityScore.paper_id == pid)
        ).first()
        assert row.explanation is None
        assert row.score is not None


def test_recompute_updates_in_place(db, monkeypatch):
    pid = _make_paper(db, repo_url="https://github.com/o/r")
    _patch(monkeypatch, signals=GOOD_SIGNALS)
    seam.score_reproducibility(pid)
    seam.score_reproducibility(pid)
    with Session(db) as s:
        repro_rows = s.exec(
            select(ReproducibilityScore).where(ReproducibilityScore.paper_id == pid)
        ).all()
        setup_rows = s.exec(select(ExperimentSetup).where(ExperimentSetup.paper_id == pid)).all()
        assert len(repro_rows) == 1
        assert len(setup_rows) == 1


def test_happy_path_mirrors_and_breakdown(db, monkeypatch):
    pid = _make_paper(db, repo_url="https://github.com/o/r")
    _patch(monkeypatch, signals=GOOD_SIGNALS)
    seam.score_reproducibility(pid)
    with Session(db) as s:
        paper = s.get(Paper, pid)
        assert paper.experiment_setup == {
            "hyperparameters": "lr=0.1",
            "datasets": "ImageNet",
            "environment": "python 3.13",
            "available": True,
        }
        row = s.exec(
            select(ReproducibilityScore).where(ReproducibilityScore.paper_id == pid)
        ).first()
        assert row.repo_exists is True
        assert row.code_quality_score == 1.0

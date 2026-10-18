"""Reproducibility scoring seam (R6, R7).

Replaces the paper-search stub at the same signature. Runs the pipeline
(inspect -> code-quality -> extract -> completeness -> score -> explain),
upserts ``ReproducibilityScore`` + ``ExperimentSetup``, mirrors the setup and
number onto the ``Paper`` in the same transaction, and returns the number.
Raises ``ReproducibilityUnavailable`` only when the repo is not inspectable AND
the setup is unavailable (R4.4, R6.4) — the orchestrator maps that to
Score_Status ``unavailable``.
"""

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.db.session import engine
from app.models.paper import Paper, ScoreStatus
from app.models.reproducibility import ExperimentSetup, ReproducibilityScore
from app.services.repro import inspector
from app.services.repro.code_quality import code_quality
from app.services.repro.completeness import completeness
from app.services.repro.explainer import explain
from app.services.repro.extractor import extract_setup
from app.services.repro.scorer import reproducibility
from app.services.repro.standards import Evidence
from app.services.repro.types import (
    ExperimentSetupData,
    ReproducibilityUnavailable,
)


def score_reproducibility(paper_id: int) -> float:
    """Compute, persist, and return the rule-based Reproducibility Score."""
    with Session(engine) as session:
        paper = session.get(Paper, paper_id)
        if paper is None:
            raise ReproducibilityUnavailable(f"paper {paper_id} not found")

        signals = inspector.inspect_repo(paper.repo_url)
        cq = code_quality(signals)

        # Setup extraction; failure => unavailable, never fabricated (R3.3).
        setup: ExperimentSetupData | None
        try:
            setup = extract_setup(paper.title, paper.abstract)
        except Exception:
            setup = None
        setup_available = setup is not None
        setup_completeness = completeness(setup)

        if not signals.inspectable and not setup_available:
            raise ReproducibilityUnavailable(f"no signal for paper {paper_id}")

        # Evaluate against the Domain's standard (R10.2). Reader-side papers have
        # no manuscript/source — manuscript_text/source_files stay None here.
        # Writer uploads populate those in a separate spec (ADR 0003).
        evidence = Evidence(
            repo=signals,
            code_quality=cq,
            setup=setup,
            setup_completeness=setup_completeness,
            manuscript_text=None,
            source_files=None,
        )
        result = reproducibility(paper.domain, evidence)
        score = result.score

        # Explanation is optional; failure must not fail the score (R5.3).
        try:
            explanation = explain(score, signals, result)
        except Exception:
            explanation = None

        _persist(
            session,
            paper,
            score=score,
            cq=cq,
            signals=signals,
            setup=setup,
            setup_available=setup_available,
            setup_completeness=setup_completeness,
            explanation=explanation,
            field_of_study=result.field_of_study,
            standard_key=result.standard_key,
            score_q=result.score_q,
            score_d=result.score_d,
            reference_versions=result.reference_versions,
            # Full per-Criterion rows. Old keys (id/title/status/evidence_note)
            # stay present so existing consumers/tests keep working.
            criteria=[
                {
                    "id": c.criterion.id,
                    "title": c.criterion.title,
                    "tag": c.criterion.tag.value,
                    "weight": c.criterion.weight,
                    "category": c.criterion.category,
                    "source_references": c.criterion.source_references,
                    "status": c.status.value,
                    "confidence": c.confidence,
                    "evidence_note": c.evidence_note,
                }
                for c in result.results
            ],
            categories=[
                {
                    "category": cat.category,
                    "score": cat.score,
                    "points_lost": cat.points_lost,
                }
                for cat in result.categories
            ],
            discrepancies=[
                {
                    "criterion_id": r.criterion.id,
                    "paper_value": r.paper_value,
                    "code_value": r.code_value,
                    "reference": "; ".join(r.criterion.source_references),
                }
                for r in result.discrepancies
            ],
        )
        session.commit()
        return score


def _persist(
    session: Session,
    paper: Paper,
    *,
    score: float,
    cq: float,
    signals,
    setup: ExperimentSetupData | None,
    setup_available: bool,
    setup_completeness: float,
    explanation: str | None,
    field_of_study: str | None,
    standard_key: str | None,
    score_q: float | None,
    score_d: float | None,
    reference_versions: dict | None,
    criteria: list[dict] | None,
    categories: list[dict] | None,
    discrepancies: list[dict] | None,
) -> None:
    """Upsert both rows and mirror onto the Paper in one transaction (R7.4)."""
    now = datetime.now(UTC)

    repro_row = session.exec(
        select(ReproducibilityScore).where(ReproducibilityScore.paper_id == paper.id)
    ).first()
    if repro_row is None:
        repro_row = ReproducibilityScore(paper_id=paper.id)
    repro_row.score = score
    repro_row.status = ScoreStatus.ready
    repro_row.code_quality_score = cq
    repro_row.repo_exists = signals.exists
    repro_row.repo_inspectable = signals.inspectable
    repro_row.setup_completeness = setup_completeness
    repro_row.explanation = explanation
    repro_row.field_of_study = field_of_study
    repro_row.standard_key = standard_key
    repro_row.score_q = score_q
    repro_row.score_d = score_d
    repro_row.reference_versions = reference_versions
    repro_row.criteria = criteria
    repro_row.categories = categories
    repro_row.discrepancies = discrepancies
    repro_row.updated_at = now
    session.add(repro_row)

    setup_row = session.exec(
        select(ExperimentSetup).where(ExperimentSetup.paper_id == paper.id)
    ).first()
    if setup_row is None:
        setup_row = ExperimentSetup(paper_id=paper.id)
    setup_row.hyperparameters = setup.hyperparameters if setup else None
    setup_row.datasets = setup.datasets if setup else None
    setup_row.environment = setup.environment if setup else None
    setup_row.available = setup_available
    setup_row.updated_at = now
    session.add(setup_row)

    # Mirror the setup JSON that paper-search's detail read expects (R6.3, R7.2).
    paper.experiment_setup = {
        "hyperparameters": setup.hyperparameters if setup else None,
        "datasets": setup.datasets if setup else None,
        "environment": setup.environment if setup else None,
        "available": setup_available,
    }
    paper.reproducibility_score = score
    paper.reproducibility_status = ScoreStatus.ready
    session.add(paper)

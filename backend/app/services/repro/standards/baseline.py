"""Baseline standard — domain-neutral default (R10.2, R10.6).

Selected when the `Field of Study` is ``unknown`` so every paper stays scorable.
A minimal, field-agnostic subset in the same weighted Q/D shape as the field
standards (Q weights sum 0.30, D+Q/D weights sum 0.70), judged deterministically
from the gatherable `Evidence` pool (R10.6): repository signals plus the
extracted `Experiment Setup`. No LLM on the roll-up path (R4.5, ADR 0009). A
repo-less paper still scores from the setup-derived criteria (R4.3).
"""

from app.services.repro.standards import (
    CategoryScore,
    Criterion,
    CriterionResult,
    CriterionStatus,
    Evidence,
    StandardResult,
    Tag,
    roll_up,
)

_FIELD = "unknown"
_KEY = "baseline"
_REFERENCE_VERSIONS = {"rule": "1.2"}

# Domain-neutral criteria. Q group (code/tool quality) sums to 0.30; the D group
# (paper-to-code agreement, here "is the setup described in the paper backed by
# artifacts") sums to 0.70. Weights are flat within each group.
_CODE_AVAILABLE = Criterion(
    id="B-Q1",
    title="Code available",
    tag=Tag.Q,
    weight=0.15,
    category="Run the Code",
    source_references=["baseline"],
)
_DOCUMENTATION = Criterion(
    id="B-Q2",
    title="Documentation present",
    tag=Tag.Q,
    weight=0.15,
    category="Run the Code",
    source_references=["baseline"],
)
_DEPENDENCIES = Criterion(
    id="B-D1",
    title="Dependencies / environment described",
    tag=Tag.D,
    weight=0.35,
    category="Reproduce the Results",
    source_references=["baseline"],
)
_DATA_REFERENCED = Criterion(
    id="B-D2",
    title="Data referenced",
    tag=Tag.D,
    weight=0.35,
    category="Reproduce the Results",
    source_references=["baseline"],
)

_Q_CRITERIA = [_CODE_AVAILABLE, _DOCUMENTATION]
_D_CRITERIA = [_DEPENDENCIES, _DATA_REFERENCED]
_CRITERIA = _Q_CRITERIA + _D_CRITERIA

# Fail fast at import if the baseline table ever drifts from the Q/D split that
# every standard shares (§6): Q sums 0.30, D + Q/D sums 0.70.
_Q_TOTAL = round(sum(c.weight for c in _Q_CRITERIA), 6)
_D_TOTAL = round(sum(c.weight for c in _D_CRITERIA), 6)
assert _Q_TOTAL == 0.300, f"Baseline Q weights must sum to 0.300, got {_Q_TOTAL}"
assert _D_TOTAL == 0.700, f"Baseline D+Q/D weights must sum to 0.700, got {_D_TOTAL}"

# Confidence bands (§5.5): repo-signal-backed judgements (repo.exists,
# repo.has_readme) are near-certain; criteria read from the extracted setup text
# are thin and get a low-to-moderate confidence.
_C_REPO = 0.9
_C_SETUP = 0.6


def _status(present: bool) -> CriterionStatus:
    return CriterionStatus.met if present else CriterionStatus.unmet


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _result(
    criterion: Criterion, present: bool, confidence: float, yes: str, no: str
) -> CriterionResult:
    # Deterministic heuristics, confidence per §5.5; no LLM (R4.5, ADR 0009).
    return CriterionResult(
        criterion=criterion,
        status=_status(present),
        confidence=confidence,
        evidence_note=yes if present else no,
    )


class BaselineStandard:
    """R10.4 adapter for unknown-field papers."""

    key = _KEY
    field_of_study = _FIELD
    reference_versions = _REFERENCE_VERSIONS

    def criteria(self) -> list[Criterion]:
        return list(_CRITERIA)

    def evaluate(self, evidence: Evidence) -> StandardResult:
        repo = evidence.repo
        setup = evidence.setup
        # A repository exists only when present and inspectable (R1.3), matching
        # the field standards. A missing repo lowers the repo-signal criteria but
        # the setup-derived criteria still contribute (R4.3) — unlike CS §5.3,
        # the baseline is domain-neutral and never zeroes the whole score.
        has_repo = repo.exists and repo.inspectable
        has_environment = _has_text(setup.environment if setup else None)
        has_datasets = _has_text(setup.datasets if setup else None)

        results = [
            _result(
                _CODE_AVAILABLE, has_repo, _C_REPO,
                "inspectable repository exists", "no inspectable repository",
            ),
            _result(
                _DOCUMENTATION, has_repo and repo.has_readme, _C_REPO,
                "README present", "no README found",
            ),
            _result(
                _DEPENDENCIES, has_environment, _C_SETUP,
                "environment described in setup", "no environment described",
            ),
            _result(
                _DATA_REFERENCED, has_datasets, _C_SETUP,
                "datasets referenced in setup", "no datasets referenced",
            ),
        ]

        score, score_q, score_d = roll_up(results)
        categories = _categories(results)
        return StandardResult(
            field_of_study=_FIELD,
            standard_key=_KEY,
            reference_versions=dict(_REFERENCE_VERSIONS),
            results=results,
            score=score,
            score_q=score_q,
            score_d=score_d,
            categories=categories,
            discrepancies=[],
        )


def _categories(results: list[CriterionResult]) -> list[CategoryScore]:
    """Per-display-category breakdown (§10.4): weighted mean and points lost."""
    by_category: dict[str, list[CriterionResult]] = {}
    for r in results:
        if r.status is CriterionStatus.not_applicable:
            continue
        by_category.setdefault(r.criterion.category, []).append(r)

    categories: list[CategoryScore] = []
    for name, rs in by_category.items():
        wsum = sum(r.criterion.weight for r in rs)
        if wsum == 0:
            continue
        score = sum(r.criterion.weight * r.adjusted() for r in rs) / wsum
        points_lost = sum(r.criterion.weight * (1.0 - r.adjusted()) for r in rs)
        categories.append(CategoryScore(category=name, score=score, points_lost=points_lost))
    return categories

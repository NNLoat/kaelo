"""Reproducibility Standard adapter — interface, shared shapes, roll-up, selection.

A `Reproducibility Score` is produced by evaluating a `Paper`'s `Evidence`
against a `Reproducibility Standard` selected by its `Domain` (R10.1, R10.2).
Every standard is one implementation of the `ReproducibilityStandard` Protocol;
`select_standard(field_of_study)` is the registry so a standard can be added or
swapped without touching the scorer or any consumer (R10.4).

The number is the deterministic, weighted, confidence-adjusted `roll_up` of the
per-`Criterion` statuses over two groups: Q (code/tool quality, 0.30) and D
(paper-to-code discrepancy, 0.70), with Q/D criteria counted in the D group
(scoring_rule.md §6). ``not_applicable`` criteria are dropped and the remaining
weights are renormalized *within each group*, preserving the 0.30/0.70 split.
There is **no LLM import on the roll-up path** (R4.5, ADR 0009) — the LLM may
only supply per-criterion evidence as data inside the concrete standards.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable

from app.models.paper import PaperDomain
from app.services.repro.types import ExperimentSetupData, RepoSignals


class CriterionStatus(str, Enum):
    """How a single Criterion was judged against the Evidence (scoring_rule.md §5)."""

    met = "met"
    partial = "partial"
    unmet = "unmet"
    not_applicable = "not_applicable"


# Raw status score s_i; not_applicable criteria are dropped before the roll-up.
_POINTS = {
    CriterionStatus.met: 1.0,
    CriterionStatus.partial: 0.5,
    CriterionStatus.unmet: 0.0,
}


class Tag(str, Enum):
    """Which scoring group a Criterion belongs to (scoring_rule.md §6)."""

    Q = "Q"  # code/tool quality -> 0.30 group
    D = "D"  # paper-to-code discrepancy -> 0.70 group
    QD = "Q/D"  # both; counted in the D (0.70) group


@dataclass(frozen=True)
class Criterion:
    """A weighted scoring-model criterion (scoring_rule.md §3.1 / §4.1)."""

    id: str  # e.g. "M-D1", "C-A5"
    title: str
    tag: Tag
    weight: float  # expert prior; per field Q sums 0.30, D+Q/D sums 0.70
    category: str  # display category (§10), e.g. "Run the Code"
    source_references: list[str]  # e.g. ["R1: item 12c"] or ["R3: Artifacts Available"]


@dataclass(frozen=True)
class CriterionResult:
    """The judgement for one Criterion of a standard (scoring_rule.md §5.5)."""

    criterion: Criterion
    status: CriterionStatus
    confidence: float  # c in [0, 1] (§5.5)
    evidence_note: str
    paper_value: str | None = None  # for D contradictions (discrepancy report, §7)
    code_value: str | None = None

    @property
    def s(self) -> float:
        """Raw status score s_i (met=1, partial=0.5, unmet=0)."""
        return _POINTS[self.status]

    def adjusted(self, base_rate: float = 0.5) -> float:
        """Confidence-adjusted score ŝ = c·s + (1−c)·π (§5.5).

        ``base_rate`` is the criterion's cohort base rate π; 0.5 when no cohort
        data exist (§5.5).
        """
        return self.confidence * self.s + (1.0 - self.confidence) * base_rate


@dataclass(frozen=True)
class Evidence:
    """Everything a standard may judge against — gathered once, role-aware.

    ``manuscript_text`` and ``source_files`` are populated only for a
    Writer-claimed paper (ADR 0003); for indexed Reader-side papers they are
    ``None``.
    """

    repo: RepoSignals
    code_quality: float
    setup: ExperimentSetupData | None
    setup_completeness: float
    manuscript_text: str | None = None
    source_files: list[tuple[str, str]] | None = None


@dataclass(frozen=True)
class CategoryScore:
    """One of the seven plain-language display categories (scoring_rule.md §10)."""

    category: str
    score: float  # S_k (§10.4)
    points_lost: float  # L_k


@dataclass(frozen=True)
class StandardResult:
    """A standard's per-Criterion judgements plus the deterministic roll-up."""

    field_of_study: str  # "medicine" / "computer_science" / "unknown"
    standard_key: str  # "tripod_ai" / "cs_merged" / "baseline"
    reference_versions: dict  # §8 version pinning
    results: list[CriterionResult]
    score: float  # weighted roll-up S (the number)
    score_q: float  # S_Q (0.30 group)
    score_d: float  # S_D (0.70 group)
    categories: list[CategoryScore]  # seven display categories (§10)
    discrepancies: list[CriterionResult] = field(default_factory=list)


@runtime_checkable
class ReproducibilityStandard(Protocol):
    """One published standard behind a single adapter interface (R10.4)."""

    key: str
    field_of_study: str
    reference_versions: dict

    def criteria(self) -> list[Criterion]:
        """The standard's weighted criteria table."""
        ...

    def evaluate(self, evidence: Evidence) -> StandardResult:
        """Judge each Criterion from ``evidence`` and roll up to a score."""
        ...


def roll_up(results: list[CriterionResult]) -> tuple[float, float, float]:
    """Weighted, confidence-adjusted Q/D roll-up (scoring_rule.md §6).

    Returns ``(S, S_Q, S_D)``. ``not_applicable`` criteria are dropped and the
    remaining weights are renormalized *within each group*, preserving the
    0.30/0.70 split. met=1, partial=0.5, unmet=0; each ŝ is confidence-adjusted
    via :meth:`CriterionResult.adjusted`. If a whole group is NA, ``S`` falls
    back to the other group's score. No LLM import (R4.5, ADR 0009).
    """
    applicable = [r for r in results if r.status is not CriterionStatus.not_applicable]
    q = [r for r in applicable if r.criterion.tag is Tag.Q]
    d = [r for r in applicable if r.criterion.tag in (Tag.D, Tag.QD)]

    def group_mean(rs: list[CriterionResult]) -> float | None:
        wsum = sum(r.criterion.weight for r in rs)
        if wsum == 0:
            return None
        return sum(r.criterion.weight * r.adjusted() for r in rs) / wsum

    s_q, s_d = group_mean(q), group_mean(d)
    if s_q is None and s_d is None:
        return 0.0, 0.0, 0.0
    if s_q is None:  # whole Q group NA -> S = S_D, flagged by caller
        return s_d, 0.0, s_d
    if s_d is None:  # whole D group NA -> S = S_Q, flagged by caller
        return s_q, s_q, 0.0
    return 0.30 * s_q + 0.70 * s_d, s_q, s_d


def select_standard(field_of_study: PaperDomain) -> ReproducibilityStandard:
    """Pick the standard for a `Paper`'s `Domain` (R10.1, R10.2).

    medicine -> TRIPOD+AI (R1, 26 criteria); computer_science -> merged CS
    (R3/R4/R5, 25 criteria); anything else (including ``unknown``) -> the
    domain-neutral baseline.

    ``field_of_study`` may be a ``PaperDomain`` enum or its string value — both
    resolve by value. Concrete standards are imported lazily so this module has
    no import-time dependency on them (they are added in task 11.2); the module
    itself stays importable on its own.
    """
    key = getattr(field_of_study, "value", field_of_study)

    if key == "medicine":
        from app.services.repro.standards.tripod_ai import TripodAiStandard

        return TripodAiStandard()
    if key == "computer_science":
        from app.services.repro.standards.cs_merged import CsMergedStandard

        return CsMergedStandard()

    from app.services.repro.standards.baseline import BaselineStandard

    return BaselineStandard()

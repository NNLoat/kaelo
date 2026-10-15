"""Reproducibility Standard adapter — interface, shared shapes, roll-up, selection.

A `Reproducibility Score` is produced by evaluating a `Paper`'s `Evidence`
against a `Reproducibility Standard` selected by its `Domain` (R10.1, R10.2).
Every standard is one implementation of the `ReproducibilityStandard` Protocol;
`select_standard(domain)` is the registry so a standard can be added or swapped
without touching the scorer or any consumer (R10.4).

The number is the deterministic ``roll_up`` of the per-Criterion statuses
(met=1 / partial=0.5 / unmet=0; not_applicable excluded). There is **no LLM
import on the roll-up path** (R4.2, R4.6) — the LLM may only supply per-criterion
evidence as data inside the concrete standards.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from app.services.repro.types import ExperimentSetupData, RepoSignals


class CriterionStatus(str, Enum):
    """How a single Criterion was judged against the Evidence."""

    met = "met"
    partial = "partial"
    unmet = "unmet"
    not_applicable = "not_applicable"


@dataclass(frozen=True)
class CriterionResult:
    """The judgement for one Criterion of a standard."""

    id: str
    title: str
    status: CriterionStatus
    evidence_note: str


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
class StandardResult:
    """A standard's per-Criterion judgements plus the deterministic roll-up."""

    standard_key: str
    criteria: list[CriterionResult]
    score: float


@runtime_checkable
class ReproducibilityStandard(Protocol):
    """One published standard behind a single adapter interface (R10.4)."""

    key: str

    def criteria(self) -> list[str]:
        """The standard's criterion ids/titles."""
        ...

    def evaluate(self, evidence: Evidence) -> StandardResult:
        """Judge each Criterion from ``evidence`` and roll up to a score."""
        ...


# Points per status; not_applicable is excluded from the denominator entirely.
_POINTS = {
    CriterionStatus.met: 1.0,
    CriterionStatus.partial: 0.5,
    CriterionStatus.unmet: 0.0,
}


def roll_up(criteria: list[CriterionResult]) -> float:
    """Deterministic score in ``[0, 1]`` from per-Criterion statuses (R4.2, R4.6).

    met=1, partial=0.5, unmet=0; ``not_applicable`` criteria are excluded from
    the denominator. Returns ``0.0`` when nothing is scorable. No LLM import.
    """
    scored = [c for c in criteria if c.status is not CriterionStatus.not_applicable]
    if not scored:
        return 0.0
    return sum(_POINTS[c.status] for c in scored) / len(scored)


def select_standard(domain: object) -> ReproducibilityStandard:
    """Pick the standard for a `Paper`'s `Domain` (R10.1, R10.2).

    computer_science -> ML Reproducibility Checklist; medicine -> FAIR;
    anything else (including ``unknown``) -> the domain-neutral baseline.

    ``domain`` may be a ``PaperDomain`` enum (added in a later task) or its
    string value — both resolve by value, so this stays importable before the
    enum exists. Concrete standards are imported lazily so this module has no
    import-time dependency on them (they are added in task 11.2).
    """
    key = getattr(domain, "value", domain)

    if key == "computer_science":
        from app.services.repro.standards.ml_checklist import MLReproducibilityChecklist

        return MLReproducibilityChecklist()
    if key == "medicine":
        from app.services.repro.standards.fair import FAIRStandard

        return FAIRStandard()

    from app.services.repro.standards.baseline import BaselineStandard

    return BaselineStandard()

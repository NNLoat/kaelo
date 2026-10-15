"""Reproducibility_Scorer — standard-based, rule-based, no LLM on the roll-up path (R4).

The number is produced by selecting the `Reproducibility Standard` for the
`Paper`'s `Domain` (R10.2) and evaluating the gathered `Evidence` against it; the
returned ``StandardResult.score`` is the deterministic ``roll_up`` of the
per-Criterion statuses (R4.2, R4.6). A repo-less paper still scores from the
setup-derived criteria (R4.3). This module imports no LLM.
"""

from app.services.repro.standards import Evidence, StandardResult, select_standard


def reproducibility(domain: object, evidence: Evidence) -> StandardResult:
    """Evaluate ``evidence`` against the standard for ``domain`` (R4.2, R10.3).

    ``domain`` may be a ``PaperDomain`` enum (added in a later task) or its
    string value — ``select_standard`` resolves either, so an ``unknown`` domain
    maps to the domain-neutral baseline and every paper stays scorable (R4.4).
    """
    standard = select_standard(domain)
    return standard.evaluate(evidence)

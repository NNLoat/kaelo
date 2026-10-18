"""Reproducibility_Scorer — weighted Standards-Conformance roll-up, no LLM (R4).

The `Reproducibility Score` is produced by selecting the `Reproducibility
Standard` for the `Paper`'s `Field of Study` (R10.3) and evaluating the gathered
`Evidence` against that standard's weighted `Criteria`. Each `Criterion` is
judged to a status (met / partial / unmet / not_applicable) with an extraction
confidence ``c``; the status scores are rolled up deterministically into

    S = 0.30·S_Q + 0.70·S_D        (R4.2, R4.4)

where ``S_Q`` is the weight-normalized, confidence-adjusted mean over the
applicable Q (code/tool-quality) criteria and ``S_D`` the same over the
applicable D and Q/D (paper-to-code discrepancy) criteria — so the Q group is
always 0.30 of the number and the D+Q/D group always 0.70. ``not_applicable``
criteria are dropped and the remaining weights renormalized *within each group*,
preserving the split; if a whole group is NA the score falls back to the other
group's score (R4.5). The returned ``StandardResult`` also carries the seven §10
display ``categories`` (R4.11), the paper-to-code ``discrepancies`` report (§7),
and the pinned ``reference_versions`` (§8) — all filled by the standard's
``evaluate`` (R4.12).

A repo-less paper still scores from whatever the remaining evidence satisfies
(the extracted `Experiment Setup`, manuscript text, source files) rather than
failing (R4.6). This module imports no LLM and does not raise on empty evidence:
the standards always return a valid StandardResult (a low one when evidence is
thin). Deciding "no score at all" belongs to the seam
(`services/reproducibility.py`), which treats a paper as unscorable only when the
repository is not inspectable *and* no Experiment Setup is available (R4.7).
"""

from app.models.paper import PaperDomain
from app.services.repro.standards import Evidence, StandardResult, select_standard


def reproducibility(
    field_of_study: PaperDomain | str, evidence: Evidence
) -> StandardResult:
    """Evaluate ``evidence`` against the standard for ``field_of_study`` (R4.2, R10.3).

    ``field_of_study`` may be a :class:`PaperDomain` enum or its string value —
    ``select_standard`` resolves either, so ``medicine`` → TRIPOD+AI, ``computer_
    science`` → merged CS, and anything else (including ``unknown``) → the
    domain-neutral baseline, keeping every paper scorable (R4.4).

    The selected standard's ``evaluate`` judges each `Criterion` and performs the
    deterministic weighted roll-up ``S = 0.30·S_Q + 0.70·S_D`` (R4.2–R4.5); the
    returned :class:`StandardResult` already carries ``score``, ``score_q``,
    ``score_d``, the per-`Criterion` ``results``, the seven display
    ``categories`` (§10.4, R4.11), the ``discrepancies`` report (§7), and the
    pinned ``reference_versions`` (§8, R4.12). A repo-less paper still scores
    from the criteria the remaining evidence satisfies (R4.6). No LLM import on
    this path.

    This function never raises on empty evidence — the standards return a valid
    (low) StandardResult. The seam decides when a paper has no score at all
    (R4.7).
    """
    standard = select_standard(field_of_study)
    return standard.evaluate(evidence)

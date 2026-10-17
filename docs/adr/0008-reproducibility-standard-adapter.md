# Reproducibility evaluation is defined by a pluggable Reproducibility Standard

Reproducibility is evaluated against a published standard selected by the Paper's
field of study, implementing the Standards-Conformance Score of `scoring_rule.md`
(v1.2): **TRIPOD+AI** (R1; 26 weighted criteria) for Medicine papers, and a single
merged **ACM Artifact Review and Badging v1.1 + ML Code Completeness Checklist +
FAIR4RS Principles v1.0** standard (R3/R4/R5; 25 weighted criteria) for Computer
Science papers, with a domain-neutral **baseline** standard for `unknown`. FAIR4RS
is one of the three *Computer Science* references, not the medical standard. Each
standard is an implementation of a single `ReproducibilityStandard` interface
exposing its weighted `criteria()` (each criterion carries a classification tag
`Q`/`D`/`Q/D`, a weight, a display category, and its source reference(s)) and an
`evaluate(evidence) -> StandardResult`; a `select_standard(field_of_study)`
registry maps field → standard. The score is the weighted, confidence-adjusted
roll-up `S = 0.30·S_Q + 0.70·S_D` (see ADR 0009). We chose a published-standard-
per-field approach over the previous ad-hoc heuristic (four repo booleans at 0.25
each + three Experiment Setup fields), which was not grounded in any recognized
reproducibility standard. The adapter seam exists so adding or swapping a standard
is a new implementation plus a registry entry, with no change to the scorer, the
review report, or the persistence layer.

## Considered Options

- **One global checklist for all papers** — rejected: CS and Medicine
  reproducibility expectations differ enough that a single list serves neither.
  `scoring_rule.md` scores the two fields with entirely different standards.
- **FAIR as the Medicine standard** — rejected: FAIR4RS is a research-*software*
  standard and is one of the three *Computer Science* references in
  `scoring_rule.md`; Medicine is scored with TRIPOD+AI, a clinical prediction-model
  reporting guideline.
- **Keep the ad-hoc heuristic** — rejected: not defensible as "reproducibility"
  and not explainable to a Reader against any external standard.

## Consequences

- The project commits to exactly two fields of study (CS, Medicine) plus an
  `unknown` baseline — matching the source scope in ADR 0001.
- The CS standard merges three references (ACM/ML/FAIR4RS) into 25 weighted
  criteria with per-criterion source references; the Medicine standard is the 26
  weighted TRIPOD+AI criteria aligned (display-only) with the Thai FDA manual.
- Both the Reproducibility Score and the manuscript-and-code Review Report
  consume the **same** standard, so the criteria are authored once.
- The per-criterion `StandardResult` (not just a float) is the shared artifact;
  the number is the weighted, confidence-adjusted roll-up of it (see ADR 0009).
- The scoring-model fidelity target is `scoring_rule.md` v1.2; the reference and
  rule versions are recorded on every result (§8 of the rule).

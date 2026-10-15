# Reproducibility evaluation is defined by a pluggable Reproducibility Standard

Reproducibility is evaluated against a published standard selected by the Paper's
domain: the **ML Reproducibility Checklist** for Computer Science papers and the
**FAIR** principles for Medicine papers, with a domain-neutral **baseline**
standard for `unknown` domains. Each standard is an implementation of a single
`ReproducibilityStandard` interface exposing its `criteria()` and an
`evaluate(evidence) -> StandardResult`; a `select_standard(domain)` registry maps
domain → standard. We chose a published-standard-per-domain approach over the
previous ad-hoc heuristic (four repo booleans at 0.25 each + three Experiment
Setup fields), which was not grounded in any recognized reproducibility standard.
The adapter seam exists so adding or swapping a standard is a new implementation
plus a registry entry, with no change to the scorer, the review report, or the
persistence layer.

## Considered Options

- **One global checklist for all papers** — rejected: CS and Medicine
  reproducibility expectations differ enough that a single list serves neither.
- **Keep the ad-hoc heuristic** — rejected: not defensible as "reproducibility"
  and not explainable to a Reader against any external standard.

## Consequences

- The project commits to exactly two domains (CS, Medicine) plus an `unknown`
  baseline — matching the source scope in ADR 0001.
- Both the Reproducibility Score and the manuscript-and-code Review Report
  consume the **same** standard, so the criteria are authored once.
- The per-criterion `StandardResult` (not just a float) is the shared artifact;
  the number is a deterministic roll-up of it (see ADR 0009).

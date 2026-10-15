# The LLM supplies per-criterion evidence as data; the score roll-up is deterministic

Richer standards (ML Reproducibility Checklist, FAIR) include criteria that pure
heuristics cannot judge — e.g. "are limitations discussed?", "is the dataset
FAIR-accessible?". For those, the LLM reads the available material and emits a
structured **per-criterion observation as data** (met / partial / unmet /
not-applicable plus a short evidence note). The criterion-status → `[0,1]` score
roll-up inside `StandardResult` is a deterministic rule; the LLM output can
never change the number. This preserves the existing boundary (the LLM extracts
and explains but never produces the score — the generalization of ADR 0004's
"score is rule-based") even as criteria become qualitative.

## Consequences

- The property "the Reproducibility Score never comes from the LLM" still holds:
  mutating or faking the LLM evidence changes criterion notes and statuses but
  the roll-up rule, given the same statuses, yields the same number.
- Evidence is treated as data, never as control flow; it is parsed into bounded
  per-criterion structures before the roll-up.
- The Review Report (code-generation) reuses the same evidence + statuses to
  write its findings, so a single evaluation feeds both the number and the
  Markdown report without a second LLM pass over the criteria.

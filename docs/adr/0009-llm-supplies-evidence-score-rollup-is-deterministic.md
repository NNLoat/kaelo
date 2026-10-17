# The LLM supplies per-criterion evidence as data; the score roll-up is deterministic

Richer standards (TRIPOD+AI for Medicine; the merged ACM/ML-Code-Completeness/
FAIR4RS standard for Computer Science) include criteria that pure heuristics
cannot judge — e.g. "are limitations and their effect on bias discussed?", "is the
software described with rich, FAIR metadata?". For those, the LLM reads the
available material and emits a structured **per-criterion observation as data**
(met / partial / unmet / not-applicable, a confidence `c`, and a short evidence
note). The criterion-status → `[0,1]` score roll-up inside `StandardResult` is a
deterministic rule — the weighted, confidence-adjusted Standards-Conformance
formula `S = 0.30·S_Q + 0.70·S_D` of `scoring_rule.md` v1.2, where each criterion's
weight, classification tag (`Q`/`D`/`Q/D`), and confidence adjustment
`ŝ = c·s + (1−c)·π` are fixed by the rule. The LLM output (status, confidence,
note) is an input to that rule; it can never change the weights, the tags, or the
formula, so it can never *produce* the number. This preserves the existing
boundary (the LLM extracts and explains but never produces the score — the
generalization of ADR 0004's "score is rule-based") even as criteria become
qualitative.

## Consequences

- The property "the Reproducibility Score never comes from the LLM" still holds:
  mutating or faking the LLM evidence changes criterion notes, statuses, and
  confidences, but the weighted roll-up rule, given the same statuses and
  confidences, yields the same number.
- Confidence `c` is itself bounded data (extractor agreement or rule specificity),
  fed into the fixed `ŝ = c·s + (1−c)·π` adjustment; the LLM cannot widen a
  criterion's weight or move it between the Q (0.30) and D (0.70) groups.
- Evidence is treated as data, never as control flow; it is parsed into bounded
  per-criterion structures before the roll-up.
- The Review Report (code-generation) reuses the same evidence + statuses to
  write its findings, so a single evaluation feeds both the number and the
  Markdown report without a second LLM pass over the criteria.

# Reproducibility Score is rule-based; the LLM extracts and explains but never invents the number

The Reproducibility Score is computed by a deterministic rule over independent
Score Signals — repo existence, repo quality (README / license / tests / recent
activity, from the Git host API), and Experiment Setup completeness (fraction of
a fixed checklist the LLM could extract). The signals are combined with
fixed-but-config-tunable weights into a single 0.0–1.0 value (surfaced to the UI
as 0–100 with a band label). The LLM's role is bounded: it extracts the
Experiment Setup and writes a human-readable explanation of the resulting score,
but it does not produce or adjust the number.

When a signal cannot be gathered (Git host unreachable or rate-limited, LLM
extraction fails), the engine computes a Partial Score from the signals that are
available and records each signal's availability status, rather than failing the
whole score.

We chose this over letting the LLM output the score directly because a rule-based
number is reproducible, auditable, and explainable — properties the product
itself is about — and because partial scoring keeps the feature resilient to
flaky external calls during a demo. The alternative (LLM-as-scorer) was rejected:
it would make the score non-deterministic and hard to defend to a researcher.

Reconsidering later means re-deriving the signal set, the weighting, and the
`ReproducibilityScore` persistence shape, so it is recorded here. Weights and
thresholds live in config and may be tuned without reopening this decision; the
*shape* (rule-based blend, LLM bounded to extract/explain, partial scoring on
signal failure) is what this ADR fixes.

"""Code_Quality_Scorer — pure, rule-based, no LLM (R2)."""

from app.services.repro.types import RepoSignals

# Equal weights over the four positive signals, normalized to [0,1]. Each flip
# false->true adds its weight, so the score is monotonic non-decreasing (R2.1).
_WEIGHTS = {
    "has_readme": 0.25,
    "has_license": 0.25,
    "has_tests": 0.25,
    "recent_activity": 0.25,
}


def code_quality(signals: RepoSignals) -> float:
    """Weighted, normalized [0,1] quality score; absent repo -> 0.0 (R2.2)."""
    if not signals.exists or not signals.inspectable:
        return 0.0
    return sum(w for name, w in _WEIGHTS.items() if getattr(signals, name))

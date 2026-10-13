"""Reproducibility_Scorer — pure, rule-based, no LLM (R4)."""


def reproducibility(
    code_quality: float,
    repo_exists: bool,  # noqa: ARG001 — part of the agreed signature; blend uses code_quality
    setup_completeness: float,
    *,
    w_repo: float,
    w_setup: float,
) -> float:
    """Deterministic weighted blend in [0,1], monotonic in each contribution.

    A non-inspectable repo yields ``code_quality == 0.0`` yet the setup
    contribution still scores the paper (R4.3). Weights come from config (R4.6).
    """
    total = w_repo + w_setup
    if total == 0:
        return 0.0
    return (w_repo * code_quality + w_setup * setup_completeness) / total

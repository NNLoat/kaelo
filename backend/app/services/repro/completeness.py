"""Setup_Completeness — pure, rule-based, no LLM (R4.1)."""

from app.services.repro.types import ExperimentSetupData

EXPECTED_FIELDS = ("hyperparameters", "datasets", "environment")


def completeness(setup: ExperimentSetupData | None) -> float:
    """Populated-field fraction over the expected fields; None -> 0.0."""
    if setup is None:
        return 0.0
    populated = sum(1 for f in EXPECTED_FIELDS if getattr(setup, f))
    return populated / len(EXPECTED_FIELDS)

"""Shared signal/data shapes for reproducibility scoring."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RepoSignals:
    """Metadata signals from a repository host (never full clone, R1.5).

    ``inspectable`` is False for absent/malformed/unsupported URLs (R1.3);
    ``failed`` is True for an API error/timeout/rate-limit (R1.4). The two are
    never conflated.
    """

    exists: bool
    has_readme: bool
    has_license: bool
    has_tests: bool
    recent_activity: bool
    inspectable: bool
    failed: bool


@dataclass
class ExperimentSetupData:
    """Extracted Experiment Setup; each field None when unsupported (R3.2)."""

    hyperparameters: str | None
    datasets: str | None
    environment: str | None


class ReproducibilityUnavailable(Exception):
    """No signal available: neither an inspectable repo nor a setup (R4.4)."""

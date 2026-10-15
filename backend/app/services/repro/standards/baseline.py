"""Baseline standard — domain-neutral default (R9.5, R10.1).

Selected when the `Domain` is ``unknown`` so every paper stays scorable. A
minimal, domain-neutral criterion set judged deterministically from the
gatherable `Evidence` pool (R10.5): repository signals plus the extracted
`Experiment Setup`. No LLM on the roll-up path (R4.5, ADR 0009). A repo-less
paper still scores from the setup-derived criteria (R4.3).
"""

from app.services.repro.standards import (
    CriterionResult,
    CriterionStatus,
    Evidence,
    StandardResult,
    roll_up,
)


def _status(present: bool) -> CriterionStatus:
    return CriterionStatus.met if present else CriterionStatus.unmet


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


class BaselineStandard:
    """R10.4 adapter for unknown-domain papers."""

    key = "baseline"

    _CRITERIA = [
        "code_available",
        "documentation",
        "dependencies_described",
        "data_referenced",
    ]

    def criteria(self) -> list[str]:
        return list(self._CRITERIA)

    def evaluate(self, evidence: Evidence) -> StandardResult:
        repo = evidence.repo
        setup = evidence.setup
        has_environment = _has_text(setup.environment if setup else None)
        has_datasets = _has_text(setup.datasets if setup else None)

        results = [
            CriterionResult(
                "code_available", "Code available",
                _status(repo.exists),
                "repository exists" if repo.exists else "no inspectable repository",
            ),
            CriterionResult(
                "documentation", "Documentation present",
                _status(repo.has_readme),
                "README present" if repo.has_readme else "no README found",
            ),
            CriterionResult(
                "dependencies_described", "Dependencies / environment described",
                _status(has_environment),
                "environment described in setup" if has_environment else "no environment described",
            ),
            CriterionResult(
                "data_referenced", "Data referenced",
                _status(has_datasets),
                "datasets referenced in setup" if has_datasets else "no datasets referenced",
            ),
        ]
        return StandardResult(self.key, results, roll_up(results))

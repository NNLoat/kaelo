"""FAIR standard — the ``medicine`` standard (R10.1).

Findable, Accessible, Interoperable, Reusable, judged deterministically from the
same gatherable `Evidence` pool (R10.5): repository signals plus the extracted
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


class FAIRStandard:
    """R10.4 adapter for medicine papers."""

    key = "fair"

    _CRITERIA = [
        "findable",
        "accessible",
        "interoperable",
        "reusable_license",
        "reusable_documentation",
        "data_referenced",
    ]

    def criteria(self) -> list[str]:
        return list(self._CRITERIA)

    def evaluate(self, evidence: Evidence) -> StandardResult:
        repo = evidence.repo
        setup = evidence.setup
        has_datasets = _has_text(setup.datasets if setup else None)
        has_environment = _has_text(setup.environment if setup else None)
        interoperable = has_datasets or has_environment

        results = [
            CriterionResult(
                "findable", "Findable",
                _status(repo.exists),
                "repository locatable" if repo.exists else "no inspectable repository",
            ),
            CriterionResult(
                "accessible", "Accessible",
                _status(repo.exists),
                "repository accessible" if repo.exists else "no accessible repository",
            ),
            CriterionResult(
                "interoperable", "Interoperable",
                _status(interoperable),
                "datasets/environment described" if interoperable else "no datasets or environment described",
            ),
            CriterionResult(
                "reusable_license", "Reusable — license",
                _status(repo.has_license),
                "license present" if repo.has_license else "no license found",
            ),
            CriterionResult(
                "reusable_documentation", "Reusable — documentation",
                _status(repo.has_readme),
                "README present" if repo.has_readme else "no README found",
            ),
            CriterionResult(
                "data_referenced", "Data referenced",
                _status(has_datasets),
                "datasets referenced in setup" if has_datasets else "no datasets referenced",
            ),
        ]
        return StandardResult(self.key, results, roll_up(results))

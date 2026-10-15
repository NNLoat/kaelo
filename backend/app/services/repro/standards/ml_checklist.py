"""ML Reproducibility Checklist — the ``computer_science`` standard (R10.1).

~6 criteria scoped to gatherable evidence (R10.5): repository signals and the
extracted `Experiment Setup`. Each criterion is a deterministic heuristic over
`Evidence`; the roll-up stays rule-based with no LLM import (R4.5, ADR 0009).
A non-inspectable repo still scores from the setup-derived criteria (R4.3).
"""

from app.services.repro.standards import (
    CriterionResult,
    CriterionStatus,
    Evidence,
    StandardResult,
    roll_up,
)


def _bool_criterion(
    cid: str, title: str, present: bool, yes: str, no: str
) -> CriterionResult:
    status = CriterionStatus.met if present else CriterionStatus.unmet
    return CriterionResult(cid, title, status, yes if present else no)


def _text_criterion(cid: str, title: str, value: str | None) -> CriterionResult:
    """A setup field: met when present, not_applicable when the setup is absent."""
    if value is None:
        return CriterionResult(cid, title, CriterionStatus.not_applicable, "no setup extracted")
    text = value.strip()
    if text:
        return CriterionResult(cid, title, CriterionStatus.met, "specified in setup")
    return CriterionResult(cid, title, CriterionStatus.unmet, "field present but empty")


class MLReproducibilityChecklist:
    """R10.4 adapter for computer-science papers."""

    key = "ml_checklist"

    _CRITERIA = [
        "code_available",
        "documentation",
        "tests_present",
        "license",
        "hyperparameters_specified",
        "datasets_specified",
        "environment_specified",
    ]

    def criteria(self) -> list[str]:
        return list(self._CRITERIA)

    def evaluate(self, evidence: Evidence) -> StandardResult:
        repo = evidence.repo
        setup = evidence.setup
        results = [
            _bool_criterion(
                "code_available", "Code availability", repo.exists,
                "repository exists", "no inspectable repository",
            ),
            _bool_criterion(
                "documentation", "README / documentation", repo.has_readme,
                "README present", "no README found",
            ),
            _bool_criterion(
                "tests_present", "Tests present", repo.has_tests,
                "tests present", "no tests found",
            ),
            _bool_criterion(
                "license", "License", repo.has_license,
                "license present", "no license found",
            ),
            _text_criterion(
                "hyperparameters_specified", "Hyperparameters specified",
                setup.hyperparameters if setup else None,
            ),
            _text_criterion(
                "datasets_specified", "Datasets specified",
                setup.datasets if setup else None,
            ),
            _text_criterion(
                "environment_specified", "Environment / dependencies",
                setup.environment if setup else None,
            ),
        ]
        return StandardResult(self.key, results, roll_up(results))

"""Medicine standard — TRIPOD+AI 2024 (scoring_rule.md §3.1, R1).

The 26 weighted criteria of TRIPOD+AI (R1), aligned to the Thai FDA manual (R2),
encoded verbatim from scoring_rule.md §3.1: exact ids (M-Q*/M-D*), tags, weights
(Q sums 0.30, D sums 0.70), the seven §10.2 display categories, and the R1 item +
R2 Thai-element source references on each.

Judged deterministically from the gatherable `Evidence` pool (R10.6): repository
signals, code_quality, setup, setup_completeness, manuscript_text, source_files.
**No LLM import on this roll-up path** (R4.5, ADR 0009); a bounded per-criterion
LLM evidence helper is permitted by §5.5 only where a pure heuristic cannot
decide, but this first iteration decides every criterion from the Evidence and
uses confidence < 1.0 for criteria read from thin text/index material (§5.5).

Applicability (§3.1) is honoured so NA can be applied by study type, but because
the ingested Evidence does not carry study type reliably in this iteration the
default is ``development-and-evaluation`` (all 26 criteria apply). The §5.4
Medicine rules (no-repo caps, code/model-access zeroing) are applied, and D
criteria scored 0 by contradiction are reported in ``StandardResult.discrepancies``.
"""

from app.services.repro.standards import (
    CategoryScore,
    Criterion,
    CriterionResult,
    CriterionStatus,
    Evidence,
    StandardResult,
    Tag,
    roll_up,
)

_FIELD = "medicine"
_KEY = "tripod_ai"
_REFERENCE_VERSIONS = {
    "R1": "TRIPOD+AI 2024",
    "R2": "Thai FDA manual 2023",
    "rule": "1.2",
}

# Study-type applicability inputs (§3.1). Default: everything applies.
STUDY_DEVELOPMENT_AND_EVALUATION = "development-and-evaluation"
STUDY_DEVELOPMENT_ONLY = "development-only"
STUDY_EVALUATION_ONLY = "evaluation-only"

# §3.1 applicability: which criteria go NA for the non-default study types.
_NA_DEVELOPMENT_ONLY = {"M-Q10"}  # E-only item
_NA_EVALUATION_ONLY = {"M-Q8", "M-Q9", "M-D1", "M-D2", "M-D3", "M-D4", "M-D9"}

# --- The 26 criteria, verbatim from scoring_rule.md §3.1 -------------------
# Q group (15 criteria) sums to 0.300; D group (11 criteria) sums to 0.700.

_Q_CRITERIA = [
    Criterion(
        id="M-Q1", tag=Tag.Q, weight=0.050,
        category="Purpose & Target Patients",
        title=(
            "Target population and intended purpose in the care pathway, "
            "including intended users"
        ),
        source_references=["R1: item 3b", "R2: §2.7 (10)", "R2: §4.1 (4)"],
    ),
    Criterion(
        id="M-Q2", tag=Tag.Q, weight=0.010,
        category="Purpose & Target Patients",
        title="Title identifies the model study, target population and outcome",
        source_references=["R1: item 1", "R2: §2.7 (11)"],
    ),
    Criterion(
        id="M-Q3", tag=Tag.Q, weight=0.010,
        category="Purpose & Target Patients",
        title="Study objectives, including development and/or validation",
        source_references=["R1: item 4", "R2: §2.7 (10)"],
    ),
    Criterion(
        id="M-Q4", tag=Tag.Q, weight=0.020,
        category="Purpose & Target Patients",
        title="Eligibility criteria for participants",
        source_references=["R1: item 6b", "R2: §2.7 (11)", "R2: §4.1 (4)"],
    ),
    Criterion(
        id="M-Q5", tag=Tag.Q, weight=0.020,
        category="Purpose & Target Patients",
        title="Outcome and time horizon clearly defined, with rationale",
        source_references=["R1: item 8a", "R2: §2.7 (11)", "R2: §4.1 (4)"],
    ),
    Criterion(
        id="M-Q6", tag=Tag.Q, weight=0.020,
        category="Data Used",
        title=(
            "Data sources described separately for development and evaluation, "
            "with representativeness"
        ),
        source_references=["R1: item 5a", "R2: §4.1 (2)"],
    ),
    Criterion(
        id="M-Q7", tag=Tag.Q, weight=0.020,
        category="Data Used",
        title="All predictors defined, including how and when measured",
        source_references=["R1: item 9b", "R2: §4.1 (2)"],
    ),
    Criterion(
        id="M-Q8", tag=Tag.Q, weight=0.020,
        category="Safe Use & Limits",
        title=(
            "How poor-quality or unavailable input data are handled on "
            "implementation"
        ),
        source_references=["R1: item 27a", "R2: §4.1 (5)"],
    ),
    Criterion(
        id="M-Q9", tag=Tag.Q, weight=0.020,
        category="Safe Use & Limits",
        title=(
            "Whether users must interact with input handling or the model, and "
            "the expertise needed"
        ),
        source_references=["R1: item 27b", "R2: §4.1 (5)"],
    ),
    Criterion(
        id="M-Q10", tag=Tag.Q, weight=0.030,
        category="Code & Model Access",
        title=(
            "For evaluation: how model predictions were calculated (formula, "
            "code, object, API)"
        ),
        source_references=["R1: item 12g", "R2: §4.1 (5)"],
    ),
    Criterion(
        id="M-Q11", tag=Tag.Q, weight=0.020,
        category="Ethics & Registration",
        title="Where the study protocol can be accessed, or that none was prepared",
        source_references=["R1: item 18c", "R2: §4.1 (6)"],
    ),
    Criterion(
        id="M-Q12", tag=Tag.Q, weight=0.020,
        category="Ethics & Registration",
        title="Registration name and number, or statement of non-registration",
        source_references=["R1: item 18d", "R2: §4.1 (6)"],
    ),
    Criterion(
        id="M-Q13", tag=Tag.Q, weight=0.020,
        category="Ethics & Registration",
        title="Ethics committee/IRB named; consent or waiver described",
        source_references=["R1: item 17", "R2: §4.1 (6)"],
    ),
    Criterion(
        id="M-Q14", tag=Tag.Q, weight=0.010,
        category="Safe Use & Limits",
        title="Approaches to model fairness and their rationale",
        source_references=["R1: item 14", "R2: §4.1 (6)"],
    ),
    Criterion(
        id="M-Q15", tag=Tag.Q, weight=0.010,
        category="Safe Use & Limits",
        title="Limitations and their effect on bias and generalizability",
        source_references=["R1: item 26", "R2: §4.1 (6)"],
    ),
]

_D_CRITERIA = [
    Criterion(
        id="M-D1", tag=Tag.D, weight=0.100,
        category="How the Model Was Built",
        title=(
            "Model type, rationale, all model-building steps, hyperparameter "
            "tuning, internal validation method"
        ),
        source_references=["R1: item 12c", "R2: §2.7 (8)", "R2: §4.1 (1)"],
    ),
    Criterion(
        id="M-D2", tag=Tag.D, weight=0.050,
        category="How the Model Was Built",
        title=(
            "Model output (probabilities/classes) and how classification "
            "thresholds were set"
        ),
        source_references=["R1: item 15", "R2: §2.7 (8)"],
    ),
    Criterion(
        id="M-D3", tag=Tag.D, weight=0.080,
        category="How the Model Was Built",
        title="How data were partitioned and used for development and evaluation",
        source_references=["R1: item 12a", "R2: §2.7 (9)", "R2: §4.1 (1)"],
    ),
    Criterion(
        id="M-D4", tag=Tag.D, weight=0.040,
        category="How the Model Was Built",
        title=(
            "How predictors were handled (functional form, rescaling, "
            "transformation)"
        ),
        source_references=["R1: item 12b", "R2: §2.7 (9)"],
    ),
    Criterion(
        id="M-D5", tag=Tag.D, weight=0.060,
        category="Data Used",
        title="Data preprocessing and quality checking",
        source_references=["R1: item 7", "R2: §2.7 (9)", "R2: §4.1 (2)"],
    ),
    Criterion(
        id="M-D6", tag=Tag.D, weight=0.070,
        category="Performance Results",
        title=(
            "All performance measures and plots used and why (discrimination, "
            "calibration, clinical utility)"
        ),
        source_references=["R1: item 12e", "R2: §4.1 (3)"],
    ),
    Criterion(
        id="M-D7", tag=Tag.D, weight=0.090,
        category="Performance Results",
        title=(
            "Performance estimates with confidence intervals, including key "
            "subgroups"
        ),
        source_references=["R1: item 23a", "R2: §4.1 (3)"],
    ),
    Criterion(
        id="M-D8", tag=Tag.D, weight=0.030,
        category="Data Used",
        title=(
            "Differences between development and evaluation data in setting, "
            "eligibility, outcome, predictors"
        ),
        source_references=["R1: item 16", "R2: §4.1 (3)"],
    ),
    Criterion(
        id="M-D9", tag=Tag.D, weight=0.080,
        category="Code & Model Access",
        title=(
            "Full model to allow third-party predictions, with access or reuse "
            "restrictions"
        ),
        source_references=["R1: item 22", "R2: §4.1 (5)"],
    ),
    Criterion(
        id="M-D10", tag=Tag.D, weight=0.060,
        category="Code & Model Access",
        title="Availability of the analytical code",
        source_references=["R1: item 18f"],
    ),
    Criterion(
        id="M-D11", tag=Tag.D, weight=0.040,
        category="Data Used",
        title="Availability of the study data",
        source_references=["R1: item 18e"],
    ),
]

_CRITERIA = _Q_CRITERIA + _D_CRITERIA
_BY_ID = {c.id: c for c in _CRITERIA}

# Fail fast at import if the encoded table ever drifts from §3.1 group totals.
_Q_TOTAL = round(sum(c.weight for c in _Q_CRITERIA), 6)
_D_TOTAL = round(sum(c.weight for c in _D_CRITERIA), 6)
assert _Q_TOTAL == 0.300, f"Medicine Q weights must sum to 0.300, got {_Q_TOTAL}"
assert _D_TOTAL == 0.700, f"Medicine D weights must sum to 0.700, got {_D_TOTAL}"
assert len(_Q_CRITERIA) == 15, "Medicine Q group must have 15 criteria"
assert len(_D_CRITERIA) == 11, "Medicine D group must have 11 criteria"


# --- scoring helpers -------------------------------------------------------

def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _met(c: float, note: str) -> tuple[CriterionStatus, float, str]:
    return CriterionStatus.met, c, note


def _partial(c: float, note: str) -> tuple[CriterionStatus, float, str]:
    return CriterionStatus.partial, c, note


def _unmet(c: float, note: str) -> tuple[CriterionStatus, float, str]:
    return CriterionStatus.unmet, c, note


# Confidence bands (§5.5): repo-signal-backed judgements are near-certain;
# text/index-only Q judgements are thin and get a low-to-moderate confidence.
_C_REPO = 0.9
_C_TEXT = 0.6
_C_THIN = 0.5


class TripodAiStandard:
    """R10.4 adapter for Medicine papers — TRIPOD+AI 2024 (R1)."""

    key = _KEY
    field_of_study = _FIELD
    reference_versions = _REFERENCE_VERSIONS

    def __init__(self, study_type: str = STUDY_DEVELOPMENT_AND_EVALUATION) -> None:
        self.study_type = study_type

    def criteria(self) -> list[Criterion]:
        return list(_CRITERIA)

    # --- applicability (§3.1) ---------------------------------------------
    def _na_ids(self) -> set[str]:
        if self.study_type == STUDY_DEVELOPMENT_ONLY:
            return set(_NA_DEVELOPMENT_ONLY)
        if self.study_type == STUDY_EVALUATION_ONLY:
            return set(_NA_EVALUATION_ONLY)
        return set()  # development-and-evaluation: all 26 apply

    def evaluate(self, evidence: Evidence) -> StandardResult:
        na_ids = self._na_ids()
        repo = evidence.repo
        setup = evidence.setup
        # A repository exists only when it is both present and inspectable (R1.3).
        has_repo = repo.exists and repo.inspectable

        has_text = _has_text(evidence.manuscript_text)
        has_hyperparams = _has_text(setup.hyperparameters if setup else None)
        has_datasets = _has_text(setup.datasets if setup else None)
        has_environment = _has_text(setup.environment if setup else None)

        results: list[CriterionResult] = []
        discrepancies: list[CriterionResult] = []

        for crit in _CRITERIA:
            if crit.id in na_ids:
                results.append(
                    CriterionResult(
                        criterion=crit,
                        status=CriterionStatus.not_applicable,
                        confidence=1.0,
                        evidence_note=f"not applicable for {self.study_type} study",
                    )
                )
                continue

            status, confidence, note, paper_value, code_value = self._judge(
                crit,
                has_repo=has_repo,
                repo=repo,
                has_text=has_text,
                has_hyperparams=has_hyperparams,
                has_datasets=has_datasets,
                has_environment=has_environment,
            )
            result = CriterionResult(
                criterion=crit,
                status=status,
                confidence=confidence,
                evidence_note=note,
                paper_value=paper_value,
                code_value=code_value,
            )
            results.append(result)
            # §5.2 / §7: a D criterion scored 0 by contradiction is a discrepancy.
            if (
                crit.tag in (Tag.D, Tag.QD)
                and status is CriterionStatus.unmet
                and (paper_value is not None or code_value is not None)
            ):
                discrepancies.append(result)

        score, score_q, score_d = roll_up(results)
        categories = _categories(results)
        return StandardResult(
            field_of_study=_FIELD,
            standard_key=_KEY,
            reference_versions=dict(_REFERENCE_VERSIONS),
            results=results,
            score=score,
            score_q=score_q,
            score_d=score_d,
            categories=categories,
            discrepancies=discrepancies,
        )

    # --- per-criterion deterministic judgement (§5.1/§5.2/§5.4) -----------
    def _judge(
        self,
        crit: Criterion,
        *,
        has_repo: bool,
        repo,
        has_text: bool,
        has_hyperparams: bool,
        has_datasets: bool,
        has_environment: bool,
    ) -> tuple[CriterionStatus, float, str, str | None, str | None]:
        """Return (status, confidence, note, paper_value, code_value).

        Deterministic over the Evidence; no LLM. §5.4 Medicine rules are applied
        for the code/model-access criteria. ``paper_value``/``code_value`` are set
        only for a D criterion scored 0 by contradiction, so it is reported as a
        discrepancy (§7).
        """
        cid = crit.id

        # §5.4: code & model access.
        if cid == "M-D9":
            # Full model for third-party predictions: needs a repository.
            if not has_repo:
                return (
                    *_unmet(_C_REPO, "no inspectable repository: full model unavailable"),
                    "model described in text" if has_text else None,
                    "no repository",
                )
            if repo.has_readme:
                return (*_met(_C_REPO, "repository with README exposes the model"), None, None)
            return (*_partial(_C_REPO, "repository present but undocumented model"), None, None)

        if cid == "M-D10":
            # Availability of the analytical code: needs a repository.
            if not has_repo:
                return (
                    *_unmet(_C_REPO, "no inspectable repository: analytical code unavailable"),
                    None,
                    "no repository",
                )
            return (*_met(_C_REPO, "analytical code available in repository"), None, None)

        if cid == "M-Q10":
            # For evaluation: how predictions were calculated.
            if has_repo:
                return (*_met(_C_REPO, "prediction code available in repository"), None, None)
            if has_text:
                # Described in text but no code -> capped at 0.5 (§5.4).
                note = "predictions described in text, no code (capped 0.5)"
                return (*_partial(_C_TEXT, note), None, None)
            return (*_unmet(_C_THIN, "no prediction method reported"), None, None)

        # §5.4: other D items that need code to verify cap at 0.5 without a repo.
        if cid == "M-D1":
            if has_repo and has_hyperparams:
                return (*_met(_C_REPO, "model build + hyperparameters in repo/setup"), None, None)
            if has_hyperparams:
                note = "hyperparameters in setup, no repo to verify (capped 0.5)"
                return (*_partial(_C_TEXT, note), None, None)
            if has_repo:
                note = "repository present but build steps not extracted (capped 0.5)"
                return (*_partial(_C_REPO, note), None, None)
            return (*_unmet(_C_THIN, "no model-building description"), None, None)

        if cid in ("M-D2", "M-D3", "M-D4"):
            # Build-pipeline D items verified against environment/hyperparameters.
            backed = has_hyperparams or has_environment
            if has_repo and backed:
                return (*_met(_C_REPO, "build detail in repo, backed by setup"), None, None)
            if backed:
                note = "build detail in setup, no repo to verify (capped 0.5)"
                return (*_partial(_C_TEXT, note), None, None)
            if has_repo:
                note = "repository present but detail not extracted (capped 0.5)"
                return (*_partial(_C_REPO, note), None, None)
            return (*_unmet(_C_THIN, "build detail not reported"), None, None)

        if cid == "M-D5":
            # Data preprocessing & quality checking.
            if has_datasets and has_repo:
                return (*_met(_C_REPO, "preprocessing in setup, backed by repository"), None, None)
            if has_datasets:
                note = "datasets in setup, preprocessing not verifiable (capped 0.5)"
                return (*_partial(_C_TEXT, note), None, None)
            if has_repo:
                note = "repository present but preprocessing not extracted (capped 0.5)"
                return (*_partial(_C_REPO, note), None, None)
            return (*_unmet(_C_THIN, "no preprocessing reported"), None, None)

        if cid == "M-D11":
            # Availability of the study data (§5.4: restricted-but-documented = 0.5).
            if has_datasets:
                note = "data described in setup; availability not confirmed (restricted/documented)"
                return (*_partial(_C_TEXT, note), None, None)
            return (*_unmet(_C_THIN, "no study-data availability stated"), None, None)

        if cid in ("M-D6", "M-D7"):
            # Performance results — read from text/supplement (Evidence: T, R).
            if has_text:
                note = "performance reported in text; not verified against code"
                return (*_partial(_C_TEXT, note), None, None)
            return (*_unmet(_C_THIN, "no performance results available in evidence"), None, None)

        if cid == "M-D8":
            # Dev-vs-eval data differences — text evidence only.
            if has_text:
                return (*_partial(_C_TEXT, "dev/eval differences described in text"), None, None)
            return (*_unmet(_C_THIN, "dev/eval data differences not reported"), None, None)

        # Q criteria read from thin index/text material (Evidence: T / T,M).
        # M-Q6/M-Q7 (Data Used) gain confidence when the setup carries datasets.
        if cid in ("M-Q6", "M-Q7"):
            if has_datasets:
                return (*_partial(_C_TEXT, "data described in setup"), None, None)
            if has_text:
                return (*_partial(_C_THIN, "data mentioned in manuscript text"), None, None)
            return (*_unmet(_C_THIN, "data not described in available evidence"), None, None)

        # All remaining Q criteria are text-only reporting items.
        if has_text:
            return (*_partial(_C_TEXT, "reported in manuscript text (thin evidence)"), None, None)
        return (*_unmet(_C_THIN, "not reported in available evidence"), None, None)


def _categories(results: list[CriterionResult]) -> list[CategoryScore]:
    """Per-display-category breakdown (§10.2/§10.4): weighted mean and points lost."""
    by_category: dict[str, list[CriterionResult]] = {}
    for r in results:
        if r.status is CriterionStatus.not_applicable:
            continue
        by_category.setdefault(r.criterion.category, []).append(r)

    categories: list[CategoryScore] = []
    for name, rs in by_category.items():
        wsum = sum(r.criterion.weight for r in rs)
        if wsum == 0:
            continue
        score = sum(r.criterion.weight * r.adjusted() for r in rs) / wsum
        points_lost = sum(r.criterion.weight * (1.0 - r.adjusted()) for r in rs)
        categories.append(CategoryScore(category=name, score=score, points_lost=points_lost))
    return categories

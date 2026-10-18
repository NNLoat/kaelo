"""Computer Science standard — merged ACM + ML Code Completeness + FAIR4RS.

The 25 weighted criteria of scoring_rule.md §4.1, encoded verbatim: exact ids
(C-A*/C-M*/C-FAIR-*), tags (Q / D / Q/D — C-A5 is Q/D and sits in the D group),
weights (Q sums 0.300, D + Q/D sums 0.700), the seven §10.3 display categories,
and the R3 (ACM Artifact Review and Badging v1.1) / R4 (ML Code Completeness
2020) / R5 (FAIR4RS v1.0) source references on each — including the merged rows
C-A1 (R3 + R5), C-M1 (R4 + R5) and C-FAIR-F1.2 (R5 F1.2 + R1.2).

Judged deterministically from the gatherable `Evidence` pool (R10.6): repository
signals, code_quality, setup, setup_completeness, manuscript_text, source_files.
**No LLM import on this roll-up path** (R4.5, ADR 0009); every criterion is
decided from the Evidence, with confidence < 1.0 for thin / metadata-only
criteria that index-only material cannot confirm (§5.5).

The §5.3 CS rules are applied: no code released ⇒ every CS criterion is 0
(including C-A1), except C-A7/C-A8 (Reproduced/Replicated) which default to NA
since no independent-study evidence exists, C-FAIR-F1.1 (NA if monolithic — the
default from index-only material) and C-FAIR-A1.2 (NA for public software). The
merged rows C-A1 / C-M1 / C-FAIR-F1.2 use their §5.3 sub-scoring; C-A5
"Exercisable" is capped at 0.5 without a badge or a sandbox run (we never run
code). D criteria scored 0 by contradiction are reported in
``StandardResult.discrepancies`` (§5.2 / §7).
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

_FIELD = "computer_science"
_KEY = "cs_merged"
_REFERENCE_VERSIONS = {
    "R3": "ACM v1.1",
    "R4": "ML Code Completeness 2020",
    "R5": "FAIR4RS v1.0",
    "rule": "1.2",
}

# --- The 25 criteria, verbatim from scoring_rule.md §4.1 -------------------
# Q group (16 criteria) sums to 0.300; D + Q/D group (9 criteria) sums to 0.700.
# C-A5 is tag Q/D and is counted in the D (0.700) group by roll_up.

_Q_CRITERIA = [
    Criterion(
        id="C-A1", tag=Tag.Q, weight=0.070,
        category="Get the Code",
        title=(
            "Artifacts archived in a publicly accessible repository with a DOI "
            "or persistent identifier, retrievable by that identifier, with "
            "metadata that stay accessible if the software disappears"
        ),
        source_references=["R3: Artifacts Available", "R5: F1", "R5: A1", "R5: A2"],
    ),
    Criterion(
        id="C-A2", tag=Tag.Q, weight=0.020,
        category="Read the Docs",
        title=(
            "Documented: inventory of artifacts plus enough description to "
            "exercise them"
        ),
        source_references=["R3: Functional, Documented"],
    ),
    Criterion(
        id="C-A6", tag=Tag.Q, weight=0.030,
        category="Read the Docs",
        title=(
            "Reusable: quality significantly exceeds minimal functionality "
            "(carefully documented, well structured for reuse)"
        ),
        source_references=["R3: Reusable"],
    ),
    Criterion(
        id="C-M1", tag=Tag.Q, weight=0.060,
        category="Install & Set Up",
        title=(
            "Dependencies specified (requirements/environment file, install "
            "instructions), with pinned versions"
        ),
        source_references=["R4: item 1, Specification of dependencies", "R5: R2"],
    ),
    Criterion(
        id="C-M4", tag=Tag.Q, weight=0.030,
        category="Get the Code",
        title="Pre-trained models hosted or linked",
        source_references=["R4: item 4, Pre-trained models"],
    ),
    Criterion(
        id="C-FAIR-F1.1", tag=Tag.Q, weight=0.005,
        category="Find, Cite & License",
        title=(
            "Components at different granularity get distinct identifiers "
            "(NA if monolithic)"
        ),
        source_references=["R5: F1.1"],
    ),
    Criterion(
        id="C-FAIR-F2", tag=Tag.Q, weight=0.010,
        category="Find, Cite & License",
        title="Software described with rich metadata (CITATION.cff, codemeta.json)",
        source_references=["R5: F2"],
    ),
    Criterion(
        id="C-FAIR-F3", tag=Tag.Q, weight=0.005,
        category="Find, Cite & License",
        title="Metadata explicitly include the software's identifier",
        source_references=["R5: F3"],
    ),
    Criterion(
        id="C-FAIR-F4", tag=Tag.Q, weight=0.005,
        category="Find, Cite & License",
        title="Metadata are FAIR, searchable and indexable",
        source_references=["R5: F4"],
    ),
    Criterion(
        id="C-FAIR-A1.1", tag=Tag.Q, weight=0.005,
        category="Get the Code",
        title="Retrieval protocol is open, free and universally implementable",
        source_references=["R5: A1.1"],
    ),
    Criterion(
        id="C-FAIR-A1.2", tag=Tag.Q, weight=0.005,
        category="Get the Code",
        title="Authentication/authorization where necessary (NA if public)",
        source_references=["R5: A1.2"],
    ),
    Criterion(
        id="C-FAIR-I1", tag=Tag.Q, weight=0.005,
        category="Install & Set Up",
        title="Reads/writes data in domain-community standard formats",
        source_references=["R5: I1"],
    ),
    Criterion(
        id="C-FAIR-I2", tag=Tag.Q, weight=0.005,
        category="Install & Set Up",
        title="Qualified references to other objects (datasets, resources)",
        source_references=["R5: I2"],
    ),
    Criterion(
        id="C-FAIR-R1", tag=Tag.Q, weight=0.015,
        category="Read the Docs",
        title="Described with accurate, relevant attributes (README completeness)",
        source_references=["R5: R1"],
    ),
    Criterion(
        id="C-FAIR-R1.1", tag=Tag.Q, weight=0.020,
        category="Find, Cite & License",
        title="Clear, accessible license",
        source_references=["R5: R1.1"],
    ),
    Criterion(
        id="C-FAIR-R3", tag=Tag.Q, weight=0.010,
        category="Find, Cite & License",
        title="Meets domain-relevant community standards",
        source_references=["R5: R3"],
    ),
]

_D_CRITERIA = [
    Criterion(
        id="C-A3", tag=Tag.D, weight=0.070,
        category="Match the Paper",
        title=(
            "Consistent: artifacts are relevant to the paper and contribute to "
            "generating its main results"
        ),
        source_references=["R3: Functional, Consistent"],
    ),
    Criterion(
        id="C-A4", tag=Tag.D, weight=0.070,
        category="Match the Paper",
        title=(
            "Complete: all components relevant to the paper are included, or "
            "documented proxies for proprietary parts"
        ),
        source_references=["R3: Functional, Complete"],
    ),
    Criterion(
        id="C-A5", tag=Tag.QD, weight=0.100,
        category="Run the Code",
        title=(
            "Exercisable: scripts/software that generate the paper's results "
            "run; included data can be accessed"
        ),
        source_references=["R3: Functional, Exercisable"],
    ),
    Criterion(
        id="C-A7", tag=Tag.D, weight=0.050,
        category="Independent Check",
        title=(
            "Results Reproduced: an independent team validated the results, in "
            "part with the authors' artifacts"
        ),
        source_references=["R3: Results Reproduced"],
    ),
    Criterion(
        id="C-A8", tag=Tag.D, weight=0.050,
        category="Independent Check",
        title=(
            "Results Replicated: an independent team validated the results "
            "without the authors' artifacts"
        ),
        source_references=["R3: Results Replicated"],
    ),
    Criterion(
        id="C-M2", tag=Tag.D, weight=0.100,
        category="Run the Code",
        title=(
            "Training code that can obtain the paper's principal results, "
            "including hyperparameters"
        ),
        source_references=["R4: item 2, Training code"],
    ),
    Criterion(
        id="C-M3", tag=Tag.D, weight=0.080,
        category="Run the Code",
        title=(
            "Evaluation code that computes the reported metrics under the "
            "paper's protocol"
        ),
        source_references=["R4: item 3, Evaluation code"],
    ),
    Criterion(
        id="C-M5", tag=Tag.D, weight=0.080,
        category="Match the Paper",
        title=(
            "README with a results table and precise commands that produce "
            "those results"
        ),
        source_references=["R4: item 5, README results table with commands"],
    ),
    Criterion(
        id="C-FAIR-F1.2", tag=Tag.D, weight=0.100,
        category="Match the Paper",
        title=(
            "The version of the code used in the paper is identifiable and "
            "linked to the paper (distinct version identifiers; detailed "
            "provenance)"
        ),
        source_references=["R5: F1.2", "R5: R1.2"],
    ),
]

_CRITERIA = _Q_CRITERIA + _D_CRITERIA
_BY_ID = {c.id: c for c in _CRITERIA}

# Fail fast at import if the encoded table ever drifts from §4.1 group totals.
_Q_TOTAL = round(sum(c.weight for c in _Q_CRITERIA), 6)
_D_TOTAL = round(sum(c.weight for c in _D_CRITERIA), 6)
assert _Q_TOTAL == 0.300, f"CS Q weights must sum to 0.300, got {_Q_TOTAL}"
assert _D_TOTAL == 0.700, f"CS D+Q/D weights must sum to 0.700, got {_D_TOTAL}"
assert len(_Q_CRITERIA) == 16, "CS Q group must have 16 criteria"
assert len(_D_CRITERIA) == 9, "CS D+Q/D group must have 9 criteria"


# --- scoring helpers -------------------------------------------------------

def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _met(c: float, note: str) -> tuple[CriterionStatus, float, str]:
    return CriterionStatus.met, c, note


def _partial(c: float, note: str) -> tuple[CriterionStatus, float, str]:
    return CriterionStatus.partial, c, note


def _unmet(c: float, note: str) -> tuple[CriterionStatus, float, str]:
    return CriterionStatus.unmet, c, note


def _na(note: str) -> tuple[CriterionStatus, float, str]:
    return CriterionStatus.not_applicable, 1.0, note


# Confidence bands (§5.5): repo-signal-backed judgements (has_readme/has_license/
# has_tests, open-protocol GitHub) are near-certain; metadata/partial judgements
# that index-only material cannot confirm get a low-to-moderate confidence.
_C_REPO = 0.9
_C_META = 0.6
_C_THIN = 0.5


class CsMergedStandard:
    """R10.4 adapter for Computer Science papers — merged ACM/ML/FAIR4RS."""

    key = _KEY
    field_of_study = _FIELD
    reference_versions = _REFERENCE_VERSIONS

    def criteria(self) -> list[Criterion]:
        return list(_CRITERIA)

    def evaluate(self, evidence: Evidence) -> StandardResult:
        repo = evidence.repo
        setup = evidence.setup
        # A repository exists only when it is both present and inspectable (R1.3).
        has_repo = repo.exists and repo.inspectable
        has_environment = _has_text(setup.environment if setup else None)
        has_hyperparams = _has_text(setup.hyperparameters if setup else None)

        results: list[CriterionResult] = []
        discrepancies: list[CriterionResult] = []

        for crit in _CRITERIA:
            status, confidence, note, paper_value, code_value = self._judge(
                crit,
                has_repo=has_repo,
                repo=repo,
                has_environment=has_environment,
                has_hyperparams=has_hyperparams,
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

    # --- per-criterion deterministic judgement (§5.2 / §5.3) --------------
    def _judge(
        self,
        crit: Criterion,
        *,
        has_repo: bool,
        repo,
        has_environment: bool,
        has_hyperparams: bool,
    ) -> tuple[CriterionStatus, float, str, str | None, str | None]:
        """Return (status, confidence, note, paper_value, code_value).

        Deterministic over the Evidence; no LLM. The §5.3 CS rules are applied.
        ``paper_value``/``code_value`` are set only for a D criterion scored 0 by
        contradiction so it is reported as a discrepancy (§7); from index-only
        material contradictions are not observable, so they stay ``None``.
        """
        cid = crit.id

        # C-A7/C-A8 (Reproduced/Replicated): require a later independent study.
        # No such evidence exists ⇒ NA, not 0, regardless of repo (§5.3).
        if cid in ("C-A7", "C-A8"):
            return (*_na("no independent reproduction/replication study available"),
                    None, None)
        # C-FAIR-F1.1: NA for single-component software; index-only material
        # cannot tell granularity apart, so default NA (§5.3).
        if cid == "C-FAIR-F1.1":
            return (*_na("single-component / granularity undeterminable from index"),
                    None, None)
        # C-FAIR-A1.2: NA for publicly accessible software (a public GitHub repo).
        if cid == "C-FAIR-A1.2":
            return (*_na("publicly accessible software: no auth required"), None, None)

        # §5.3: no code released ⇒ every remaining CS criterion is 0 (incl. C-A1).
        # This is a real observation, not missing evidence, so it is scored with
        # full confidence (c=1.0) — the roll-up then lands on exactly 0 with no
        # base-rate smoothing.
        if not has_repo:
            return (*_unmet(1.0, "no code released: criterion scored 0 (§5.3)"),
                    None, None)

        # --- a repository exists and is inspectable --------------------------

        # Merged row C-A1 (§5.3): archival + resolving DOI ⇒ 1; persistent but
        # non-archival link (a plain GitHub URL) ⇒ 0.5; none ⇒ 0. Evidence only
        # carries a GitHub repo_url, so a present repo is non-archival ⇒ 0.5.
        if cid == "C-A1":
            return (*_partial(_C_REPO, "non-archival GitHub link, no DOI (capped 0.5, §5.3)"),
                    None, None)

        # Merged row C-M1 (§5.3): dependency file + pinned versions + install ⇒ 1;
        # deps without versions or versions without install ⇒ 0.5; none ⇒ 0.
        # Index-only material cannot confirm pinning, so cap at 0.5 when an
        # environment is described, else 0.
        if cid == "C-M1":
            if has_environment:
                return (*_partial(_C_META, "environment described; pinning unverifiable (§5.3)"),
                        None, None)
            return (*_unmet(_C_REPO, "no dependency/environment information"), None, None)

        # Merged row C-FAIR-F1.2 (§5.3): tag/release/commit cited in the paper AND
        # repo links back ⇒ 1; only one ⇒ 0.5; neither ⇒ 0. Index-only material
        # cannot confirm the linkage ⇒ at most 0.5 when a repo exists.
        if cid == "C-FAIR-F1.2":
            return (*_partial(_C_META, "repo present; paper-version link unverifiable (0.5, §5.3)"),
                    None, None)

        # C-A5 (Exercisable, Q/D): capped at 0.5 without a badge or a successful
        # sandbox run — we never run code (§5.3). Repo exists ⇒ 0.5.
        if cid == "C-A5":
            return (*_partial(_C_META, "repo present; not run, no badge (capped 0.5, §5.3)"),
                    None, None)

        # C-A2 (Documented): README present ⇒ met, else unmet.
        if cid == "C-A2":
            if repo.has_readme:
                return (*_met(_C_REPO, "README documents the artifacts"), None, None)
            return (*_unmet(_C_REPO, "no README found"), None, None)

        # C-A6 (Reusable): README + tests ⇒ met; README only ⇒ partial; else unmet.
        if cid == "C-A6":
            if repo.has_readme and repo.has_tests:
                return (*_met(_C_REPO, "documented and tested: structured for reuse"), None, None)
            if repo.has_readme:
                return (*_partial(_C_REPO, "documented but no tests (partial reuse)"), None, None)
            return (*_unmet(_C_REPO, "neither README nor tests"), None, None)

        # C-A3 / C-A4 (Consistent / Complete, D): cannot fully verify against the
        # paper from index material ⇒ partial when a repo exists. §5.2: no
        # observable contradiction, so left partial (not a discrepancy).
        if cid in ("C-A3", "C-A4"):
            return (*_partial(_C_META, "repo present; relevance/completeness unverifiable"),
                    None, None)

        # C-M2 (Training code, D): tests + hyperparameters ⇒ met; repo only ⇒ partial.
        if cid == "C-M2":
            if repo.has_tests and has_hyperparams:
                return (*_met(_C_REPO, "code present with hyperparameters in setup"), None, None)
            return (*_partial(_C_META, "repo present; training-code match unverifiable from index"),
                    None, None)

        # C-M3 (Evaluation code, D): repo present ⇒ partial (unverifiable).
        if cid == "C-M3":
            return (*_partial(_C_META, "repo present; evaluation-code match unverifiable"),
                    None, None)

        # C-M4 (Pre-trained models, Q): cannot confirm hosting from index ⇒ partial.
        if cid == "C-M4":
            return (*_partial(_C_META, "repo present; model hosting unconfirmable from index"),
                    None, None)

        # C-M5 (README results table + commands, D): README present ⇒ partial.
        if cid == "C-M5":
            if repo.has_readme:
                return (*_partial(_C_META, "README present; results table/commands unverifiable"),
                        None, None)
            return (*_unmet(_C_REPO, "no README to carry a results table/commands"), None, None)

        # C-FAIR-F2 / F3 / F4 (metadata, Q): CITATION.cff / codemeta / identifier
        # cannot be confirmed from index-only material ⇒ partial.
        if cid in ("C-FAIR-F2", "C-FAIR-F3", "C-FAIR-F4"):
            return (*_partial(_C_META, "repo present; rich metadata not confirmable from index"),
                    None, None)

        # C-FAIR-A1.1 (open retrieval protocol, Q): GitHub over HTTPS is open,
        # free and universally implementable ⇒ met when a repo exists.
        if cid == "C-FAIR-A1.1":
            return (*_met(_C_REPO, "GitHub/HTTPS is an open, free, universal protocol"),
                    None, None)

        # C-FAIR-I1 / I2 (standard formats / qualified references, Q): not
        # confirmable from index-only material ⇒ partial.
        if cid in ("C-FAIR-I1", "C-FAIR-I2"):
            return (*_partial(_C_META, "repo present; formats/qualified refs unconfirmable"),
                    None, None)

        # C-FAIR-R1 (README attributes, Q): README present ⇒ met, else unmet.
        if cid == "C-FAIR-R1":
            if repo.has_readme:
                return (*_met(_C_REPO, "README describes the software with relevant attributes"),
                        None, None)
            return (*_unmet(_C_REPO, "no README found"), None, None)

        # C-FAIR-R1.1 (clear, accessible license, Q): license present ⇒ met.
        if cid == "C-FAIR-R1.1":
            if repo.has_license:
                return (*_met(_C_REPO, "a license is present in the repository"), None, None)
            return (*_unmet(_C_REPO, "no license found"), None, None)

        # C-FAIR-R3 (domain community standards, Q): README present ⇒ partial.
        if cid == "C-FAIR-R3":
            if repo.has_readme:
                return (*_partial(_C_META, "documented; community-standard conformance unclear"),
                        None, None)
            return (*_unmet(_C_REPO, "no documentation to assess community standards"), None, None)

        # Defensive default (should be unreachable: every id is handled above).
        return (*_unmet(_C_THIN, "no applicable heuristic"), None, None)


def _categories(results: list[CriterionResult]) -> list[CategoryScore]:
    """Per-display-category breakdown (§10.3/§10.4): weighted mean and points lost."""
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

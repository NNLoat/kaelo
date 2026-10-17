# Requirements Document

## Introduction

The `reproducibility-scoring` feature computes the `Reproducibility Score` for a
`Paper` — the component the `paper-search` feature currently stubs. It replaces
that stub behind the same seam, so when it ships the search ranking's
reproducibility term becomes real with no change to `paper-search` plumbing.

The `Reproducibility Score` is **rule-based** and is produced by evaluating a
`Paper` against a published `Reproducibility Standard` selected by the `Paper`'s
`Field of Study`. The scoring model is the **Standards-Conformance Score** defined
in `scoring_rule.md` (v1.2). The two fields of study are scored by different,
non-interchangeable standards:

- **Medicine** → **TRIPOD+AI** (R1 in the rule): one scoring standard, 26 weighted
  `Criterion`s, aligned (for display only) with the Thai FDA medical-device manual
  (R2).
- **Computer Science** → **three** references merged into **25 weighted
  `Criterion`s**: **ACM Artifact Review and Badging v1.1** (R3), the **ML Code
  Completeness Checklist** (R4), and the **FAIR4RS Principles v1.0** (R5).
- a domain-neutral **baseline** standard when the `Field of Study` is `unknown`,
  so every `Paper` stays scorable.

FAIR4RS is one of the three *Computer Science* references; it is **not** the
medical standard. Each standard is one implementation of a single `Reproducibility
Standard` adapter interface, selected by a `select_standard(field_of_study)`
registry, so a standard can be added or swapped without changing the scorer, the
persistence layer, or any consumer. See
`docs/adr/0008-reproducibility-standard-adapter.md`.

Every `Criterion` carries four scoring-model attributes drawn from `scoring_rule.md`:

- a **classification tag** — `Q` (code/tool quality), `D` (paper-to-code
  discrepancy), or `Q/D` (both; counted in the D group);
- a **weight** (an expert-assigned prior) such that, within each field, all `Q`
  weights sum to `0.30` and all `D` + `Q/D` weights sum to `0.70`;
- a plain-language **display category** (seven per field, display-only; §10 of the
  rule);
- one or more **source references** (the standard item(s) the `Criterion` is drawn
  from, e.g. "R1: item 12c" or "R3: Artifacts Available; R5: F1, A1, A2").

Evaluating a `Paper` against its standard yields a `Standard Result`: a
per-`Criterion` **status** (met=1 / partial=0.5 / unmet=0 / not-applicable=excluded)
with an evidence note and an extraction **confidence** `c`, plus the
weighted, confidence-adjusted roll-up `S = 0.30·S_Q + 0.70·S_D` in `[0,1]` that is
the `Reproducibility Score`. NA criteria are removed and weights renormalized
**within each group**, preserving the 0.30/0.70 split. Each standard draws on the
same evidence pool: the repository signals (via the `Repo_Inspector`), the
LLM-extracted `Experiment Setup`, and — for a Writer's claimed paper — the
persisted manuscript/source. The `Code-Quality Score` and `Setup_Completeness`
remain contributing signals that feed criteria.

The division of labor between AI and non-AI is deliberate and mandatory: the LLM
(Amazon Bedrock via LangChain) **extracts** the structured `Experiment Setup`,
may supply **per-criterion evidence as data** for criteria that heuristics cannot
judge, and **can explain** a computed score in natural language — but it **never
produces the number**. The criterion-status → score roll-up is a deterministic
rule; the LLM output can never change the float. See
`docs/adr/0009-llm-supplies-evidence-score-rollup-is-deterministic.md`. This
mirrors `paper-search`, where the LLM assesses relevance but the `Final Score`
blend is non-AI.

The `Field of Study` (`Domain`) that selects the standard is captured at ingestion
from the source's own field classifier (OpenAlex field id, arXiv category) and
persisted on the `Paper` as a backend column; it is never inferred later from
title/abstract. The scoring model and its persisted `Standard Result` always
record which `Field of Study` was scored. See
`docs/adr/0007-domain-captured-at-ingestion-from-source-classifiers.md`.

Scoring is asynchronous and its result is cached on the `Paper`, reusing the
Score_Status lifecycle (`pending` → `ready`/`unavailable`) that `paper-search`
established. This spec introduces the `ReproducibilityScore` and `ExperimentSetup`
tables and the Git-host repository-inspection and Experiment-Setup-extraction
business logic.

The work is layered into three concerns, matching the convention set by the
`accounts` and `paper-search` specs — Backend (FastAPI integration points,
persistence of `ReproducibilityScore` and `ExperimentSetup`, and the async
orchestration that unstubs the `paper-search` seam), Business Logic (the Git-host
repository inspector and `Code-Quality Score`, the LLM `Experiment Setup`
extractor, the Experiment-Setup completeness measure, and the rule-based
`Reproducibility Score` function), and Frontend (the detail-view surfaces for the
score breakdown and the `Experiment Setup`, which `paper-search` already renders
and this spec populates with real data). The frontend concern is light: the
`paper-search` detail view already has the score-breakdown and Experiment Setup
sections; this spec specifies what real data fills them and any explanation
affordance.

Scope is limited to computing, persisting, surfacing, and explaining the
`Reproducibility Score` and the `Experiment Setup` for a `Paper`. Finding and
caching the `Paper` itself (`paper-search`), code generation (`code-generation`),
Writer uploads (`writer-workspace`), and the search ranking math (owned by
`paper-search`) are out of scope; where this spec references the search seam or
the `Final Score`, it specifies only its own side of the boundary.

## Glossary

- **Scoring_System**: The reproducibility-scoring subsystem introduced by this
  spec, spanning the backend persistence and orchestration, the business-logic
  scorers and extractor, and the detail-view surfaces that display and explain
  the score.
- **Scoring_API**: The backend (FastAPI) integration layer that persists the
  `ReproducibilityScore` and `ExperimentSetup`, orchestrates the asynchronous
  computation, implements the `score_reproducibility(paper_id)` seam that
  `paper-search` calls, and serves the score breakdown and explanation on the
  `Paper` detail response.
- **Repo_Inspector**: The business-logic component that, given a repository link,
  queries the Git host API for the repo-quality signals (README presence, license
  presence, tests presence, recent activity) and reports whether the repository
  exists.
- **Code_Quality_Scorer**: The rule-based business-logic function that computes
  the `Code-Quality Score` in the range 0 to 1 from the signals the
  `Repo_Inspector` returns. Non-AI.
- **Setup_Extractor**: The LLM (Amazon Bedrock via LangChain) business-logic
  component that extracts a structured `Experiment Setup` from the available paper
  material (abstract and link metadata for a Reader `Paper`). Produces the derived
  artifact; never produces the score number.
- **Setup_Completeness**: The rule-based measure, in the range 0 to 1, of how
  complete an `Experiment Setup` is relative to the expected fields
  (hyperparameters, datasets, environment). Non-AI.
- **Reproducibility_Scorer**: The rule-based business-logic function that computes
  the `Reproducibility Score` in the range 0 to 1 by evaluating the `Paper`
  against its selected `Reproducibility Standard` and rolling up the per-`Criterion`
  confidence-adjusted scores by the weighted `S = 0.30·S_Q + 0.70·S_D` rule. Non-AI
  (the roll-up); may consume LLM-supplied evidence as data.
- **Field of Study** (**Domain**): The academic field a `Paper` belongs to —
  `computer_science`, `medicine`, or `unknown` — used to select the
  `Reproducibility Standard`. Captured at ingestion from the source classifier,
  persisted on the `Paper`, and recorded on every `Standard Result`.
- **Reproducibility Standard**: A published set of weighted reproducibility
  `Criterion`s a `Paper` is evaluated against, selected by its `Field of Study`:
  **TRIPOD+AI** for Medicine (R1, 26 criteria), the merged **ACM badges + ML Code
  Completeness Checklist + FAIR4RS** for Computer Science (R3/R4/R5, 25 criteria),
  or a domain-neutral **baseline** for unknown. One implementation of a single
  adapter interface. Mirrors the two fields of `scoring_rule.md`.
- **Standard_Selector**: The `select_standard(field_of_study)` registry that maps a
  `Field of Study` to its `Reproducibility Standard` implementation. The single
  place a standard is swapped or added.
- **Criterion**: One weighted item of a `Reproducibility Standard`, carrying an id,
  title, **classification tag** (`Q`/`D`/`Q/D`), **weight**, **display category**,
  and **source reference(s)**. Evaluating a `Paper` against a standard yields a
  status, evidence note, and confidence per `Criterion`.
- **Classification Tag**: A `Criterion`'s group — `Q` (code/tool quality), `D`
  (paper-to-code discrepancy), or `Q/D` (both; counted in the D group). Determines
  which group's `0.30`/`0.70` total the `Criterion`'s weight contributes to.
- **Criterion Weight**: The expert-assigned prior for a `Criterion`. Within each
  field, `Q` weights sum to `0.30` and `D`+`Q/D` weights sum to `0.70`. NA criteria
  are removed and remaining weights renormalized within their group.
- **Display Category**: One of seven plain-language groups per field (§10 of the
  rule) that a `Criterion` belongs to, used to show a non-expert reader which angle
  a `Paper` lost points on. Display-only: it never changes a weight or the score.
- **Criterion Status**: The outcome of one `Criterion` for a `Paper`: met (1),
  partial (0.5), unmet (0), or not-applicable (excluded from its group's
  denominator), with a short evidence note. May be supplied by the LLM as data;
  never the score number.
- **Criterion Confidence**: The extraction confidence `c` in `[0,1]` for a
  `Criterion`. The confidence-adjusted score is `ŝ = c·s + (1−c)·π` where `π` is a
  field/venue base rate (default `0.5`), per §5.5 of the rule.
- **Standard Result**: The structured output of evaluating a `Paper` against its
  `Reproducibility Standard`: the `Field of Study` and standard key, the full
  per-`Criterion` list (id, title, tag, weight, category, source reference(s),
  status, confidence, evidence note), the per-group scores `S_Q`/`S_D`, the
  per-display-category breakdown, and the weighted roll-up `S` (the
  `Reproducibility Score`). The shared artifact consumed by both scoring and the
  code-generation Review Report.
- **Score_Explainer**: The LLM (Bedrock via LangChain) component that produces a
  short natural-language explanation of an already-computed `Reproducibility
  Score` from its input signals. Explains the number; never changes it.
- **Paper**: A scientific publication cached by `paper-search`. The subject of a
  `Reproducibility Score`. Introduced by `paper-search`; consumed here.
- **Experiment Setup**: The structured, machine-readable description of how to
  reproduce a `Paper`'s results (hyperparameters, datasets, environment),
  extracted by the `Setup_Extractor`. Stored as a derived artifact, not full
  text.
- **Code-Quality Score**: A rating in the range 0 to 1 of the quality of a
  `Paper`'s associated repository, produced by the `Code_Quality_Scorer`. An
  input to the `Reproducibility Score`.
- **Reproducibility Score**: A rule-based rating in the range 0 to 1 of how
  reproducible a `Paper` is, produced by the `Reproducibility_Scorer` as the
  weighted, confidence-adjusted roll-up `S = 0.30·S_Q + 0.70·S_D` of the
  per-`Criterion` scores from evaluating the `Paper` against its selected
  `Reproducibility Standard`. Consumed by `paper-search` as the reproducibility
  component of the `Final Score`.
- **Standards-Conformance Score**: The name of the scoring model defined in
  `scoring_rule.md` (v1.2), which this spec implements: the `Q`/`D`-weighted,
  confidence-adjusted, per-field standard-conformance score.
- **Score_Status**: The state of a derived value on a cached `Paper`: `pending`
  while being computed, `ready` once attached, or `unavailable` if it could not be
  computed. Established by `paper-search` and reused here.
- **Score seam**: The `score_reproducibility(paper_id)` function that
  `paper-search` calls to obtain the reproducibility component. This spec replaces
  the `paper-search` stub implementation of this seam.

## Requirements

### Requirement 1: Repository Inspection (Business Logic)

**User Story:** As the backend, I want to inspect a paper's repository via the Git
host API, so that I can gather the repo-quality signals the score depends on.

#### Acceptance Criteria

1. WHEN the Repo_Inspector is given a repository link that identifies a repository on a supported Git host, THE Repo_Inspector SHALL query the Git host API and report whether the repository exists.
2. WHEN the Repo_Inspector confirms a repository exists, THE Repo_Inspector SHALL report, as discrete signals, whether a README is present, whether a license is present, whether tests are present, and whether the repository has had recent activity within a configured recency window.
3. IF the given repository link is absent, malformed, or does not identify a repository on a supported Git host, THEN THE Repo_Inspector SHALL report the repository as not inspectable and SHALL NOT fabricate repo-quality signals.
4. IF the Git host API call fails, times out, or reports rate limiting, THEN THE Repo_Inspector SHALL report the inspection as failed, distinct from a repository that was inspected and found to lack a signal.
5. THE Repo_Inspector SHALL read only repository metadata and structure signals through the Git host API and SHALL NOT clone, store, or persist repository source code, consistent with the index-only rule for Reader-side content.
6. THE Repo_Inspector SHALL read the Git host API configuration (base URL and any credential or token) from the environment and SHALL NOT read those values from committed source.

### Requirement 2: Code-Quality Scoring (Business Logic)

**User Story:** As the backend, I want a rule-based code-quality score, so that
repository signals become a single comparable number without the LLM producing
it.

#### Acceptance Criteria

1. WHEN the Code_Quality_Scorer is given the repo-quality signals for an existing repository, THE Code_Quality_Scorer SHALL compute a Code-Quality Score in the range 0 to 1 by a deterministic rule over those signals, where more positive signals never produce a lower score than fewer positive signals.
2. WHEN the Code_Quality_Scorer is given signals indicating a repository that does not exist or was not inspectable, THE Code_Quality_Scorer SHALL yield the lowest Code-Quality Score for the repository-absent case.
3. THE Code_Quality_Scorer SHALL compute the Code-Quality Score by rule and SHALL NOT call the LLM.
4. WHEN the Code_Quality_Scorer is given identical signals twice, THE Code_Quality_Scorer SHALL return identical Code-Quality Scores (deterministic).

### Requirement 3: Experiment Setup Extraction (Business Logic)

**User Story:** As the backend, I want the LLM to extract a structured Experiment
Setup from a paper's available material, so that setup completeness can be
measured and the setup can be shown.

#### Acceptance Criteria

1. WHEN the Setup_Extractor is given a Paper's available material, THE Setup_Extractor SHALL return a structured Experiment Setup with fields for hyperparameters, datasets, and environment, each field populated when the material supports it and marked absent when it does not, via Amazon Bedrock through LangChain called from the backend.
2. WHEN the Setup_Extractor cannot find information for a field, THE Setup_Extractor SHALL mark that field absent and SHALL NOT fabricate values for it.
3. IF the Setup_Extractor call fails or times out, THEN THE Scoring_System SHALL record the Experiment Setup as unavailable for that Paper, distinct from an Experiment Setup that was extracted and found incomplete.
4. THE Setup_Extractor SHALL produce only the derived structured Experiment Setup and SHALL NOT store the Paper's full text, consistent with the index-only rule for Reader-side content.
5. THE Setup_Extractor SHALL read the Bedrock/LangChain configuration (model and credentials) from the environment and SHALL NOT read those values from committed source.

### Requirement 4: Standard-Based Reproducibility Scoring (Business Logic)

**User Story:** As the backend, I want a rule-based reproducibility score that
evaluates a paper against a published standard selected by its field of study,
using the weighted Q/D Standards-Conformance model from `scoring_rule.md`, so that
the number reflects recognized reproducibility criteria and is never invented by
the LLM.

#### Acceptance Criteria

1. WHEN the Setup_Completeness measure is given an Experiment Setup, THE Setup_Completeness SHALL compute a value in the range 0 to 1 equal to the fraction of expected fields (hyperparameters, datasets, environment) that are populated, by a deterministic rule, as a contributing signal to the standard's criteria.
2. WHEN the Reproducibility_Scorer is given a Paper's Field of Study and its gathered evidence (repository signals, Code-Quality Score, extracted Experiment Setup, and any available manuscript/source), THE Reproducibility_Scorer SHALL select the applicable Reproducibility Standard via the Standard_Selector and evaluate the Paper against each Criterion, assigning each a status (met=1, partial=0.5, unmet=0, not-applicable) and a confidence `c` in [0,1].
3. THE Reproducibility_Scorer SHALL compute each Criterion's confidence-adjusted score `ŝ = c·s + (1−c)·π`, where `π` is the Criterion's field base rate (default 0.5 when no cohort data exist), per §5.5 of `scoring_rule.md`.
4. THE Reproducibility_Scorer SHALL compute the Reproducibility Score as `S = 0.30·S_Q + 0.70·S_D` in the range 0 to 1, where `S_Q` is the weight-normalized mean of `ŝ` over applicable Q Criteria and `S_D` is the weight-normalized mean of `ŝ` over applicable D and Q/D Criteria, so that all Q Criteria contribute 0.30 of the score and all D and Q/D Criteria contribute 0.70.
5. WHEN one or more Criteria are not-applicable (per the applicability rules in §3.1, §5.3, and §5.4 of `scoring_rule.md`), THE Reproducibility_Scorer SHALL exclude them and renormalize the remaining Criterion weights within their own group (Q or D), preserving the 0.30/0.70 split; IF an entire group is not-applicable, THE Reproducibility_Scorer SHALL set the Score to the other group's score and flag the excluded group.
6. WHEN the Reproducibility_Scorer is given a Paper with no inspectable repository but other available evidence (e.g. an extracted Experiment Setup), THE Reproducibility_Scorer SHALL still compute a Reproducibility Score from the Criteria that the available evidence can satisfy rather than failing.
7. IF no evidence at all is available for a Paper (the repository is not inspectable AND the Experiment Setup is unavailable AND no manuscript/source is available), THEN THE Reproducibility_Scorer SHALL report that no Reproducibility Score can be computed rather than returning a fabricated value.
8. FOR every D and Q/D Criterion, THE Reproducibility_Scorer SHALL apply the paper-to-code discrepancy rule (§5.2 of `scoring_rule.md`): a paper-stated value found and matching in the code scores 1, a value reachable through shipped config/flags counts as supported (1), a reported-but-unverifiable value scores 0.5, and an absent or contradicted value scores 0 and is recorded in the discrepancy report.
9. WHERE a Criterion cannot be judged by a pure heuristic, THE Reproducibility_Scorer MAY consume LLM-supplied per-Criterion evidence as data, but THE weighted status → score roll-up SHALL be deterministic and SHALL NOT be produced or altered by the LLM.
10. WHEN the Reproducibility_Scorer is given identical Field of Study, evidence, per-Criterion statuses, and confidences twice, THE Reproducibility_Scorer SHALL return identical Reproducibility Scores (deterministic roll-up).
11. THE Reproducibility_Scorer SHALL produce, alongside the Reproducibility Score, a Standard Result recording the Field of Study, the selected standard key, each Criterion's id, title, classification tag, weight, display category, source reference(s), status, confidence, and evidence note, the per-group scores `S_Q` and `S_D`, the seven per-display-category scores and points lost, and any discrepancy-report entries, for persistence and reuse by dependent features.
12. THE Reproducibility_Scorer SHALL apply the standard-specific scoring rules of `scoring_rule.md` — including the CS rules of §5.3 (no code released ⇒ all CS criteria 0; the merged-row rules for C-A1 / C-M1 / C-FAIR-F1.2; capping C-A5 "Exercisable" at 0.5 without a badge or sandbox run; defaulting C-A7 / C-A8 "Reproduced/Replicated" to not-applicable) and the Medicine rules of §5.4 (no code repository ⇒ M-D9 / M-D10 = 0; applicability of development-only vs evaluation-only vs development-and-evaluation studies).

### Requirement 5: Score Explanation (Business Logic)

**User Story:** As a Reader, I want a plain-language explanation of a paper's
reproducibility score, so that I understand what drove it without the explanation
changing the number.

#### Acceptance Criteria

1. WHEN the Score_Explainer is given a computed Reproducibility Score together with its input signals, THE Score_Explainer SHALL return a short natural-language explanation referencing those signals, via Amazon Bedrock through LangChain.
2. THE Score_Explainer SHALL treat the Reproducibility Score as a fixed input and SHALL NOT alter, recompute, or override the number.
3. IF the Score_Explainer call fails or times out, THEN THE Scoring_System SHALL return the Reproducibility Score and its signals without an explanation rather than failing the score.

### Requirement 6: Asynchronous Scoring and the paper-search Seam (Backend)

**User Story:** As the paper-search feature, I want the real reproducibility
scorer behind the existing seam, so that search ranking uses a real score with no
other change to paper-search.

#### Acceptance Criteria

1. THE Scoring_API SHALL implement the `score_reproducibility(paper_id)` seam that `paper-search` calls, replacing the stub, and SHALL preserve the seam's signature and its Score_Status contract so that `paper-search` requires no change beyond adopting the real implementation.
2. WHEN the seam is invoked for a Paper, THE Scoring_API SHALL inspect the repository via the Repo_Inspector, compute the Code-Quality Score, extract the Experiment Setup via the Setup_Extractor, measure Setup_Completeness, and compute the Reproducibility Score via the Reproducibility_Scorer.
3. WHEN the Reproducibility Score computation completes for a Paper, THE Scoring_API SHALL attach the Reproducibility Score to the cached Paper with Score_Status `ready` so that `paper-search` recomputes the Final Score from available components.
4. IF the Reproducibility Score cannot be computed for a Paper, THEN THE Scoring_API SHALL set that Paper's reproducibility Score_Status to `unavailable` and SHALL NOT leave it `pending` indefinitely.
5. WHEN the Scoring_API computes reproducibility for a Paper, THE Scoring_API SHALL run the work asynchronously using FastAPI BackgroundTasks consistent with the paper-search scoring orchestration, and SHALL NOT block a search or detail response on its completion.
6. WHILE the Reproducibility Score for a Paper has not yet been computed, THE Scoring_API SHALL report its Score_Status as `pending`, reusing the paper-search lifecycle.
7. THE Scoring_API SHALL compute the Reproducibility Score number by the rule-based Reproducibility_Scorer and SHALL NOT derive the number from the LLM.

### Requirement 7: Score and Experiment Setup Persistence (Backend)

**User Story:** As a developer of dependent features, I want the reproducibility
score and the experiment setup persisted and attached to the Paper, so that
code-generation and the detail view can rely on them.

#### Acceptance Criteria

1. THE Scoring_API SHALL persist a ReproducibilityScore for a Paper recording the Reproducibility Score value, the scored Field of Study, the selected standard key, the per-group scores `S_Q` and `S_D`, the full per-Criterion Standard Result (each Criterion's id, title, classification tag, weight, display category, source reference(s), status, confidence, and evidence note), the seven per-display-category scores and points lost, any discrepancy-report entries, the contributing Code-Quality Score, the repository-existence signal, the Setup_Completeness value, and each value's Score_Status, associated with the Paper by its stable identifier.
2. THE Scoring_API SHALL persist the extracted ExperimentSetup for a Paper recording the hyperparameters, datasets, and environment fields and which fields are absent, associated with the Paper by its stable identifier.
3. THE Scoring_System SHALL introduce the ReproducibilityScore and ExperimentSetup tables through an Alembic migration committed under `backend/alembic/versions/`, and SHALL NOT create those tables through runtime schema generation (create_all).
4. WHEN reproducibility is recomputed for a Paper that already has a persisted ReproducibilityScore or ExperimentSetup, THE Scoring_API SHALL update the existing record for that Paper rather than persisting a duplicate.
5. THE Scoring_API SHALL store only the derived ExperimentSetup and repository signals and SHALL NOT store the Paper's full text or the repository's source code, consistent with the index-only rule for Reader-side content.
6. IF a required database, Git-host, or Bedrock configuration value is absent from the environment variables at startup, THEN THE Scoring_System SHALL fail to start and SHALL NOT read that value from committed source.

### Requirement 8: Score Breakdown and Experiment Setup on the Detail View (Frontend)

**User Story:** As a Reader, I want the paper detail view to show the real
reproducibility breakdown, the experiment setup, and an explanation, so that I can
judge and understand a paper's reproducibility.

#### Acceptance Criteria

1. WHEN the Scoring_API has computed a Reproducibility Score for a Paper, THE detail view SHALL display the Reproducibility Score, the name of the Reproducibility Standard it was evaluated against, and its contributing Code-Quality Score and Setup_Completeness, each labeled, in place of the previously stubbed value.
2. WHILE the Reproducibility Score for a Paper has Score_Status `pending`, THE detail view SHALL display it as pending rather than a numeric value, reusing the paper-search Score_Status rendering.
3. WHEN the Reproducibility Score for a Paper has Score_Status `unavailable`, THE detail view SHALL display it as unavailable rather than a numeric value.
4. WHEN an Experiment Setup has been extracted for a Paper, THE detail view SHALL populate the Experiment Setup section with its hyperparameters, datasets, and environment, marking each absent field as not provided.
5. WHEN the Experiment Setup for a Paper is unavailable, THE detail view SHALL indicate that the Experiment Setup could not be extracted rather than showing an empty section.
6. WHEN a Score_Explainer explanation is available for a Paper, THE detail view SHALL display the explanation alongside the score breakdown.
7. IF no repository is associated with a Paper, THEN THE detail view SHALL indicate the repository-absent condition in the breakdown so the Reader can see it lowered the score.
8. WHEN a Standard Result has been computed for a Paper, THE detail view SHALL display the per-Criterion list — each Criterion's title, its status (met / partial / unmet / not-applicable), and its evidence note — so the Reader can see which criteria drove the score.

### Requirement 9: Domain Capture at Ingestion (Backend)

**User Story:** As the backend, I want each Paper's academic Domain captured and
persisted at ingestion, so that reproducibility scoring can select the right
standard without inferring the domain later.

#### Acceptance Criteria

1. WHEN a Paper is ingested from OpenAlex, THE ingestion SHALL read the source's field classifier (`primary_topic.field.id`: 17 → `computer_science`, 27 → `medicine`) and record the Paper's Domain accordingly.
2. WHEN a Paper is ingested from arXiv, THE ingestion SHALL read the source's category (`cs.*` → `computer_science`, `q-bio.*` → `medicine`) and record the Paper's Domain accordingly.
3. IF a Paper's source classifier is missing, ambiguous, or maps to neither mandated domain, THEN THE ingestion SHALL record the Paper's Domain as `unknown` and SHALL NOT fabricate a domain.
4. THE Paper SHALL persist its Domain as a column, introduced through an Alembic migration committed under `backend/alembic/versions/`, with existing rows backfilled to `unknown`.
5. WHEN a Paper's Domain is `unknown`, THE Standard_Selector SHALL select the domain-neutral baseline standard so the Paper remains scorable.

### Requirement 10: Reproducibility Standard Adapter (Business Logic)

**User Story:** As a developer, I want each reproducibility standard behind a
single adapter interface selected by field of study, so that adding or swapping a
standard touches minimal code and both scoring and the review report use the same
criteria.

#### Acceptance Criteria

1. THE Scoring_System SHALL define a single Reproducibility Standard interface exposing the standard's Field of Study, its weighted Criteria (each with id, title, classification tag, weight, display category, and source reference(s)), and an evaluation that, given a Paper's gathered evidence, returns a Standard Result (per-Criterion statuses, confidences, and evidence notes plus the deterministic weighted roll-up).
2. THE Scoring_System SHALL provide a `select_standard(field_of_study)` registry mapping `medicine` → the TRIPOD+AI standard (R1), `computer_science` → the merged ACM-badges + ML-Code-Completeness + FAIR4RS standard (R3/R4/R5), and `unknown` → the baseline standard.
3. THE Medicine standard SHALL carry the 26 Criteria of §3.1 of `scoring_rule.md` with their exact tags, weights, display categories, and R1/R2 source references; THE Computer Science standard SHALL carry the 25 Criteria of §4.1 with their exact tags, weights, display categories, and R3/R4/R5 source references; in each field the Q weights SHALL sum to 0.30 and the D plus Q/D weights SHALL sum to 0.70.
4. THE Reproducibility_Scorer SHALL obtain the applicable standard only through the Standard_Selector and SHALL NOT embed field-specific criteria logic itself.
5. WHEN a new Reproducibility Standard is added, THE change SHALL be a new implementation of the interface plus a registry entry, and SHALL NOT require changes to the Reproducibility_Scorer, the persistence layer, or any consumer of the Standard Result.
6. THE Criteria of each standard SHALL be scoped to evidence the system can actually gather (repository signals, Experiment Setup, abstract/link metadata, and — for a Writer's claimed paper — persisted manuscript/source), and SHALL NOT require paper full text that is not available under the index-only rule.
7. THE Scoring_System SHALL record, with every Standard Result, the version of each reference it scored against (TRIPOD+AI 2024; ACM v1.1; ML Code Completeness 2020; FAIR4RS v1.0) and the scoring-rule version (1.2), per §8 of `scoring_rule.md`.

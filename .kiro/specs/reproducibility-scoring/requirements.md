# Requirements Document

## Introduction

The `reproducibility-scoring` feature computes the `Reproducibility Score` for a
`Paper` — the component the `paper-search` feature currently stubs. It replaces
that stub behind the same seam, so when it ships the search ranking's
reproducibility term becomes real with no change to `paper-search` plumbing.

The `Reproducibility Score` is **rule-based**, derived from two signal groups:

1. **Repository signals** — whether an associated code repository exists and its
   `Code-Quality Score`, computed from repo-quality heuristics (README presence,
   license presence, tests presence, and recent activity) read via the Git host
   API.
2. **Experiment Setup completeness** — how complete the LLM-extracted
   `Experiment Setup` is (hyperparameters, datasets, environment) relative to the
   fields a reproducible paper is expected to describe.

The division of labor between AI and non-AI is deliberate and mandatory: the LLM
(Amazon Bedrock via LangChain) **extracts** the structured `Experiment Setup`
from the available paper material and **can explain** a computed score in natural
language, but it **never produces the number**. The `Reproducibility Score` and
the `Code-Quality Score` are computed by rule-based functions over the signals
above. This mirrors `paper-search`, where the LLM assesses relevance but the
`Final Score` blend is non-AI.

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
  the `Reproducibility Score` in the range 0 to 1 by combining the `Code-Quality
  Score` (and repo existence) with the `Setup_Completeness`. Non-AI.
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
  reproducible a `Paper` is, produced by the `Reproducibility_Scorer` from the
  repository signals and the `Setup_Completeness`. Consumed by `paper-search` as
  the reproducibility component of the `Final Score`.
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

### Requirement 4: Setup Completeness and Reproducibility Scoring (Business Logic)

**User Story:** As the backend, I want a rule-based reproducibility score that
combines repository quality and setup completeness, so that the number reflects
both signals and is never invented by the LLM.

#### Acceptance Criteria

1. WHEN the Setup_Completeness measure is given an Experiment Setup, THE Setup_Completeness SHALL compute a value in the range 0 to 1 equal to the fraction of expected fields (hyperparameters, datasets, environment) that are populated, by a deterministic rule.
2. WHEN the Reproducibility_Scorer is given a Code-Quality Score (with repository existence) and a Setup_Completeness value, THE Reproducibility_Scorer SHALL compute a Reproducibility Score in the range 0 to 1 by a deterministic rule that is non-decreasing in each input, reading any blend weights from configuration.
3. WHEN the Reproducibility_Scorer is given a Paper with no inspectable repository but an extracted Experiment Setup, THE Reproducibility_Scorer SHALL still compute a Reproducibility Score from the setup-completeness contribution rather than failing.
4. IF both the repository is not inspectable and the Experiment Setup is unavailable, THEN THE Reproducibility_Scorer SHALL report that no Reproducibility Score can be computed rather than returning a fabricated value.
5. THE Reproducibility_Scorer and the Setup_Completeness measure SHALL compute their values by rule and SHALL NOT call the LLM.
6. WHEN the Reproducibility_Scorer is given identical inputs twice, THE Reproducibility_Scorer SHALL return identical Reproducibility Scores (deterministic).

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

1. THE Scoring_API SHALL persist a ReproducibilityScore for a Paper recording the Reproducibility Score value, the contributing Code-Quality Score, the repository-existence signal, the Setup_Completeness value, and each value's Score_Status, associated with the Paper by its stable identifier.
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

1. WHEN the Scoring_API has computed a Reproducibility Score for a Paper, THE detail view SHALL display the Reproducibility Score and its contributing Code-Quality Score and Setup_Completeness, each labeled, in place of the previously stubbed value.
2. WHILE the Reproducibility Score for a Paper has Score_Status `pending`, THE detail view SHALL display it as pending rather than a numeric value, reusing the paper-search Score_Status rendering.
3. WHEN the Reproducibility Score for a Paper has Score_Status `unavailable`, THE detail view SHALL display it as unavailable rather than a numeric value.
4. WHEN an Experiment Setup has been extracted for a Paper, THE detail view SHALL populate the Experiment Setup section with its hyperparameters, datasets, and environment, marking each absent field as not provided.
5. WHEN the Experiment Setup for a Paper is unavailable, THE detail view SHALL indicate that the Experiment Setup could not be extracted rather than showing an empty section.
6. WHEN a Score_Explainer explanation is available for a Paper, THE detail view SHALL display the explanation alongside the score breakdown.
7. IF no repository is associated with a Paper, THEN THE detail view SHALL indicate the repository-absent condition in the breakdown so the Reader can see it lowered the score.

# Requirements Document

## Introduction

The `reproducibility-scoring` feature computes a **Reproducibility Score** for a
`Paper` and the structured **Experiment Setup** that underpins it. It is the
third spec in the build order (after `accounts` and a stub-scored `paper-search`)
and it is what turns ranking from a text-relevance-only sort into the blended
`Final Score = 0.7·relevance + 0.3·reproducibility` that the product is built
around.

The score is **rule-based** (see `docs/adr/0004`): it is a deterministic blend
of independent **Score Signals** — repo existence, repo quality (via the Git host
API), and Experiment Setup completeness — combined with fixed, config-tunable
weights into a single `0.0–1.0` value, surfaced to the UI as `0–100` with a band
label. The LLM's role is bounded: it extracts the Experiment Setup from the
manuscript/source and writes a human-readable explanation of the number, but it
never produces or adjusts the number itself. When a signal cannot be gathered,
the engine computes a **Partial Score** from what is available rather than
failing outright.

This spec is layered as **Backend** (FastAPI endpoints, persistence via Alembic,
background execution, Git host and Bedrock/LangChain integrations) and
**Business Logic** (a thin, utils-style `Score_Engine` the backend calls to
compute the number from gathered signals — mirroring how the `accounts` spec's
`Credential_Helper` is a thin helper the `Auth_API` calls). It introduces the
`ReproducibilityScore` and `ExperimentSetup` tables.

The **score-display UI** (breakdown on result cards and the Paper detail view) is
**out of scope** here and is owned by `paper-search`. This spec also does not
host full text or run generated code; it stores only the derived score and
Experiment Setup artifact, consistent with the index-only rule.

## Glossary

- **Scoring_System**: The reproducibility-scoring subsystem introduced by this
  spec, spanning the backend endpoints, the persistence and background execution,
  the external integrations, and the business-logic score computation.
- **Scoring_API**: The backend (FastAPI) layer that exposes the trigger and read
  endpoints, enqueues background scoring, persists `ReproducibilityScore` and
  `ExperimentSetup`, and calls the external integrations and the `Score_Engine`.
- **Score_Engine**: The business-logic layer — a thin, utility-style module the
  `Scoring_API` calls — that computes the rule-based Reproducibility Score from
  already-gathered Score Signals and the configured weights. It performs no I/O:
  it is given signal values and returns the number plus a per-signal breakdown.
  (Analogous to the `Credential_Helper` in the `accounts` spec.)
- **Repo_Inspector**: The backend integration that queries the Git host API
  (GitHub) for the Repo-Quality Signal: README, license, tests, and recent
  activity. Degrades gracefully for non-GitHub hosts and on API failure.
- **Setup_Extractor**: The backend integration that calls Amazon Bedrock through
  LangChain to extract the structured Experiment Setup and to write the score
  explanation. It never emits the score number.
- **Reproducibility Score**: A rule-based `0.0–1.0` rating of how reproducible a
  `Paper` is, blended from the Score Signals with config-tunable weights, cached
  on the `Paper`, and used as the reproducibility component of the Final Score.
- **Score Signal**: One independent input to the Reproducibility Score — repo
  existence, Repo-Quality, or Setup-Completeness — each carrying a value and an
  availability status (`ok` / `unavailable`).
- **Repo-Quality Signal**: The Score Signal derived from the Git host API:
  presence of README, license, tests, and recent commit activity.
- **Setup-Completeness Signal**: The Score Signal measuring the fraction of a
  fixed Experiment Setup checklist (hyperparameters, datasets,
  environment/dependencies, hardware, training/eval procedure) the LLM extracted.
- **Experiment Setup**: The structured, machine-readable description of how to
  reproduce a `Paper`'s results, extracted by the `Setup_Extractor` and persisted
  as a derived artifact (not full text).
- **Partial Score**: A Reproducibility Score computed from only the available
  Score Signals when one or more could not be gathered; the breakdown records
  which were skipped.
- **Score Status**: The lifecycle state of a `Paper`'s score: `pending` (queued
  or running), `ready` (computed, possibly a Partial Score), or `failed` (no
  signals could be gathered at all).

## Requirements

### Requirement 1: Trigger Scoring (Backend)

**User Story:** As the frontend application (on behalf of a Reader or Writer), I
want to request a Reproducibility Score for a Paper, so that scoring runs without
blocking the request.

#### Acceptance Criteria

1. WHEN the Scoring_API receives a scoring request for an existing Paper that has no score or whose Score Status is `failed`, THE Scoring_API SHALL set the Paper's Score Status to `pending`, enqueue a background scoring job, and return a response reporting `pending` within 2 seconds.
2. IF the Scoring_API receives a scoring request for a Paper identifier that does not exist, THEN THE Scoring_API SHALL reject the request with a not-found response and SHALL NOT enqueue a job.
3. IF the Scoring_API receives a scoring request for a Paper whose Score Status is already `pending`, THEN THE Scoring_API SHALL return the current `pending` status and SHALL NOT enqueue a duplicate job.
4. IF the Scoring_API receives a scoring request for a Paper whose Score Status is `ready` and the request does not ask for recomputation, THEN THE Scoring_API SHALL return the existing score unchanged and SHALL NOT enqueue a job.
5. WHEN the Scoring_API receives a scoring request for a Paper whose Score Status is `ready` and the request explicitly asks for recomputation, THE Scoring_API SHALL set the Score Status to `pending`, enqueue a new background scoring job, and return `pending`.
6. WHERE the acting caller is identified by a Session, THE Scoring_API SHALL accept the scoring request for any Reader or Writer without requiring a mode-specific permission, since both modes may trigger scoring.

### Requirement 2: Read Score and Breakdown (Backend)

**User Story:** As the frontend application, I want to read a Paper's current
score, its per-signal breakdown, and its explanation, so that I can show the
reproducibility component and justify it to the user.

#### Acceptance Criteria

1. WHEN the Scoring_API receives a read request for a Paper with a `ready` Score Status, THE Scoring_API SHALL return the Reproducibility Score as a `0.0–1.0` value, a `0–100` display value, a band label, the per-signal breakdown, and the explanation.
2. WHEN the Scoring_API returns a per-signal breakdown, THE Scoring_API SHALL include, for each Score Signal, its contribution value, its configured weight, and its availability status (`ok` or `unavailable`).
3. WHEN the Scoring_API receives a read request for a Paper whose Score Status is `pending`, THE Scoring_API SHALL return a response reporting `pending` without a score value.
4. WHEN the Scoring_API receives a read request for a Paper whose Score Status is `ready` and whose score is a Partial Score, THE Scoring_API SHALL return the score and SHALL identify in the breakdown every signal marked `unavailable`.
5. WHEN the Scoring_API receives a read request for a Paper whose Score Status is `failed`, THE Scoring_API SHALL return a response reporting `failed` and the reason, without a score value.
6. IF the Scoring_API receives a read request for a Paper that has never been scored, THEN THE Scoring_API SHALL return a response indicating that no score exists for the Paper.

### Requirement 3: Compute the Reproducibility Score (Business Logic)

**User Story:** As the backend, I want a thin, utils-style Score_Engine that
computes the number from gathered signals, so that scoring logic is reusable,
deterministic, and independently testable — the way the Credential_Helper serves
the Auth_API.

#### Acceptance Criteria

1. WHEN the Score_Engine is given the set of Score Signal values and the configured weights, THE Score_Engine SHALL return a Reproducibility Score in the inclusive range `0.0` to `1.0` and a per-signal breakdown, and SHALL perform no network or database I/O.
2. THE Score_Engine SHALL compute the Reproducibility Score as the weighted blend of the available Score Signals using weights read from configuration, and SHALL NOT obtain the number from the LLM.
3. WHEN the Score_Engine is given the same signal values and the same weights twice, THE Score_Engine SHALL return identical Reproducibility Score values (deterministic computation).
4. WHEN one or more Score Signals are marked `unavailable`, THE Score_Engine SHALL compute a Partial Score by renormalizing over the available signals' weights and SHALL mark the excluded signals in the breakdown.
5. IF every Score Signal is marked `unavailable`, THEN THE Score_Engine SHALL report that no score can be computed rather than returning a value, so the Scoring_API can set Score Status to `failed`.
6. WHEN the Score_Engine returns a Reproducibility Score, THE Score_Engine SHALL also return a `0–100` display value and a band label derived from fixed, configured thresholds, so the display representation is consistent across the system.
7. WHEN the Score_Engine computes the Repo-Quality Signal contribution, THE Score_Engine SHALL derive it from the presence of README, license, tests, and recent activity as supplied, treating each as an independent sub-signal.
8. WHEN the Score_Engine computes the Setup-Completeness Signal contribution, THE Score_Engine SHALL compute it as the fraction of the fixed Experiment Setup checklist fields marked present (hyperparameters, datasets, environment/dependencies, hardware, training/eval procedure).

### Requirement 4: Gather the Repo-Quality Signal (Backend)

**User Story:** As the Scoring_System, I want to inspect a Paper's code
repository through the Git host API, so that repo existence and repo quality
feed the score.

#### Acceptance Criteria

1. WHEN the Repo_Inspector is given a Paper with a GitHub repository link, THE Repo_Inspector SHALL query the GitHub API for the presence of a README, a license, tests, and recent commit activity, and SHALL return those as the Repo-Quality Signal with status `ok`.
2. WHERE a `GITHUB_TOKEN` is present in the environment, THE Repo_Inspector SHALL authenticate GitHub API requests with it to raise the rate limit, and WHERE it is absent THE Repo_Inspector SHALL make unauthenticated requests.
3. IF a Paper has a repository link on a host other than GitHub, THEN THE Repo_Inspector SHALL contribute only the repo-existence portion of the signal and SHALL mark the host-specific repo-quality sub-signals `unavailable`.
4. IF a Paper has no repository link, THEN THE Repo_Inspector SHALL report repo existence as false and the Repo-Quality Signal contribution as its defined minimum, with status `ok`.
5. IF the GitHub API is unreachable, returns an error, or reports rate-limit exhaustion, THEN THE Repo_Inspector SHALL mark the Repo-Quality Signal `unavailable` and SHALL NOT fail the overall scoring job.
6. THE Repo_Inspector SHALL NOT persist repository file contents or full source, consistent with the index-only rule for indexed Papers.

### Requirement 5: Extract the Experiment Setup and Explain the Score (Backend)

**User Story:** As the Scoring_System, I want the LLM to extract a structured
Experiment Setup and explain the resulting score, so that the completeness signal
and a human-readable justification exist without the LLM inventing the number.

#### Acceptance Criteria

1. WHEN the Setup_Extractor is given a Paper's available material (abstract and metadata for indexed Papers, or uploaded manuscript/source where present), THE Setup_Extractor SHALL call Amazon Bedrock through LangChain to extract an Experiment Setup addressing the fixed checklist fields.
2. WHEN the Setup_Extractor returns an Experiment Setup, THE Setup_Extractor SHALL mark each checklist field as present or absent, so the Setup-Completeness Signal can be computed.
3. WHEN the score has been computed, THE Setup_Extractor SHALL produce a human-readable explanation that references the per-signal breakdown, and THE explanation SHALL NOT contain a score number that differs from the Score_Engine's computed value.
4. IF the Bedrock call fails, times out, or returns an unparseable result, THEN THE Setup_Extractor SHALL mark the Setup-Completeness Signal `unavailable` and SHALL allow scoring to proceed as a Partial Score.
5. THE Setup_Extractor SHALL persist only the derived Experiment Setup artifact and SHALL NOT persist indexed-source full text, consistent with the index-only rule.
6. THE Scoring_System SHALL read Bedrock/AWS credentials from environment configuration and SHALL NOT read them from committed source.

### Requirement 6: Execute Scoring Asynchronously and Cache the Result (Backend)

**User Story:** As the Scoring_System, I want scoring to run in the background and
cache on the Paper, so that the UI can show `pending` first and read the result
when ready.

#### Acceptance Criteria

1. WHEN a background scoring job runs, THE Scoring_System SHALL gather the Score Signals via the Repo_Inspector and Setup_Extractor, call the Score_Engine, and persist the resulting Reproducibility Score, breakdown, Experiment Setup, and explanation against the Paper.
2. WHEN a background scoring job completes with at least one available Score Signal, THE Scoring_System SHALL set the Paper's Score Status to `ready`.
3. IF a background scoring job finds every Score Signal `unavailable`, THEN THE Scoring_System SHALL set the Paper's Score Status to `failed` and record the reason.
4. WHILE a background scoring job is in progress, THE Scoring_System SHALL keep the Paper's Score Status `pending` so concurrent read requests report `pending`.
5. WHEN scoring for a Paper completes, THE Scoring_System SHALL make the cached score available to a subsequent read without recomputation until an explicit recompute is requested.
6. IF a background scoring job raises an unexpected error after being enqueued, THEN THE Scoring_System SHALL set the Paper's Score Status to `failed` with the reason and SHALL NOT leave the Paper stuck in `pending`.

### Requirement 7: Persistence and Schema (Backend)

**User Story:** As a developer of dependent features, I want the score and
Experiment Setup persisted through committed migrations, so that `paper-search`
ranking and `code-generation` can rely on them.

#### Acceptance Criteria

1. THE Scoring_System SHALL introduce the `ReproducibilityScore` and `ExperimentSetup` tables through an Alembic migration committed under `backend/alembic/versions/`, and SHALL NOT create them through runtime schema generation (create_all).
2. THE Scoring_System SHALL persist each ReproducibilityScore associated with exactly one Paper, storing the `0.0–1.0` value, the per-signal breakdown with availability statuses, the Score Status, and a timestamp.
3. THE Scoring_System SHALL persist each ExperimentSetup associated with exactly one Paper, storing the checklist fields and their present/absent markers.
4. WHEN a Paper is re-scored, THE Scoring_System SHALL replace the Paper's prior ReproducibilityScore and ExperimentSetup with the recomputed result rather than accumulating stale duplicates.
5. IF a required database, Git host, or Bedrock configuration value is absent from the environment at startup, THEN THE Scoring_System SHALL fail to start and SHALL NOT read that value from committed source.

### Requirement 8: Score Design, Benefit, and Reliability (Design-level)

**User Story:** As a researcher using either mode, I want the score to be
designed, beneficial, and reliable, so that I can trust it to inform a decision
rather than mislead me.

#### Acceptance Criteria

1. THE Scoring_System SHALL define the Reproducibility Score as a documented, rule-based blend of the Score Signals with the weights, thresholds, and band labels recorded in configuration and summarized in the design, so the score's construction is explicit and auditable.
2. WHEN a Reader reads a Paper's score, THE Scoring_System SHALL present the number together with its per-signal breakdown and explanation, so the Reader can judge reproducibility and compare Papers on the same basis.
3. WHEN a Writer scores a Paper they claim, THE Scoring_System SHALL present the same breakdown so the Writer can see which signals lower the score and where to improve reproducibility.
4. THE Scoring_System SHALL compute identical Reproducibility Score values for identical signal inputs and configuration (reliability through determinism), independent of the LLM's non-deterministic text output.
5. THE Scoring_System SHALL mark any signal it could not gather as `unavailable` in the breakdown rather than substituting a guessed value, so a Partial Score is never silently presented as a complete one.
6. THE Scoring_System SHALL bound the LLM's role to extracting the Experiment Setup and explaining the score, so an LLM error can lower confidence in the explanation or the completeness signal but can never change the computed number.

## Out of Scope

- The score-display UI (result-card badges, Paper detail breakdown) — owned by
  `paper-search`.
- Executing or verifying any code — the score reasons about repository signals
  and extracted setup only.
- Code generation from the Experiment Setup — owned by `code-generation`.
- Non-GitHub host-specific repo-quality heuristics beyond repo existence.

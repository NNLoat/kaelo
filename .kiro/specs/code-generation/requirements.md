# Requirements Document

## Introduction

The `code-generation` feature lets a `User` produce candidate code for a `Paper`,
opt-in and off by default. It covers all three Code Generation cases from the
product glossary:

- **Generate** (`Reader`, Paper has no repository): produce source code from
  scratch, grounded in the Paper's `Experiment_Setup`, plus a README overview.
- **Align** (`Reader`, Paper has a repository): refine and annotate the
  *existing* repository so it matches the `Experiment_Setup` and README — not
  generated from scratch.
- **Writer generation** (`Writer`): generate from the `Writer`'s uploaded
  manuscript text and, when present, uploaded source code.

The system **never executes or verifies** generated code (see `product.md`).
Every artifact carries an "unverified, not executed" disclaimer.

Code generation is **asynchronous**: a `User` starts a `Generation_Job`, polls
its status, and retrieves the resulting `Generation` when it succeeds. Each
`Generation` is a *derived* artifact — a set of generated files (code plus a
README) with an `Artifact_Code_Quality_Score` — persisted and referenced to the
`Paper` by its index identifier, never storing external full text or external
repository contents. This is consistent with the index-only rule
(`docs/adr/0001`), the Writer-uploads carve-out (`docs/adr/0003`), and the
decision that generated code never feeds a Paper's Reproducibility Score
(`docs/adr/0004`). All AI calls go through Amazon Bedrock via LangChain from the
backend (`docs/adr/0002`).

This spec **consumes** the `Experiment_Setup` and the Paper-level
`Reproducibility_Score` as existing inputs; it does **not** extract the
`Experiment_Setup` or compute the Paper-level `Reproducibility_Score`. It depends
on the `accounts` spec for `User` identity and `Reader`/`Writer` modes, and on
`Writer` uploads being persisted. The work follows the layering convention set by
`accounts`: Frontend (React UI), Backend (FastAPI endpoints, persistence, job
lifecycle), and Business Logic (thin, provider-agnostic LangChain/Bedrock
helpers for generation and for artifact code-quality scoring).

Out of scope: extracting the `Experiment_Setup`; computing the Paper-level
`Reproducibility_Score`; executing or testing generated code; editing generated
files in the UI; a user-facing target-language selector; sharing a `Generation`
between `User`s; and any global opt-in account setting.

## Glossary

- **Codegen_System**: The code-generation subsystem introduced by this spec,
  spanning the frontend UI, the backend endpoints and job lifecycle, and the
  business-logic helpers that produce and score artifacts.
- **Codegen_API**: The backend (FastAPI) layer that exposes endpoints to start a
  `Generation_Job`, poll its status, fetch and download a `Generation`, and
  delete a `Generation`; it owns job lifecycle and `Generation` persistence.
- **Codegen_UI**: The frontend (React) layer that renders the per-action
  generation trigger, job status, the read-only artifact view, the download
  control, the displayed `Artifact_Code_Quality_Score`, and the unverified
  disclaimer.
- **Generation_Helper**: The backend business-logic layer that constructs prompts
  and calls Bedrock via LangChain to produce candidate code and a README. Thin
  and provider-agnostic per `docs/adr/0002`.
- **Scoring_Helper**: The backend business-logic layer that calls Bedrock via
  LangChain to assess the produced artifact, returning an
  `Artifact_Code_Quality_Score` and a short rationale. No static-analysis
  toolchain is used.
- **User**: An authenticated account (from the `accounts` spec). Every `User` can
  act in `Reader` or `Writer` mode.
- **Reader**: A mode in which a `User` generates (Generate) or aligns (Align)
  code for an indexed `Paper` written by others.
- **Writer**: A mode in which a `User` generates code for a paper they claim,
  from their uploaded manuscript and optional uploaded source.
- **Paper**: A scientific publication indexed from an external `Source`,
  identified by an index identifier. May or may not carry a repository link.
- **Experiment_Setup**: The structured, machine-readable description of how to
  reproduce a Paper's results, produced by a separate feature and **consumed** by
  this spec as an existing, already-persisted input.
- **Case**: Which of the three generation flows applies — **Generate**,
  **Align**, or **Writer generation**.
- **Generation_Job**: The asynchronous unit of work that produces a `Generation`.
  Started on explicit per-action opt-in. Ends in exactly one terminal state:
  **succeeded**, **failed**, or **refused**. At most one in-flight (pending or
  running) Job exists per (`User`, `Paper`, `Case`).
- **Generation**: The persisted, derived artifact a succeeded `Generation_Job`
  produces: a set of generated files (code plus a README), an
  `Artifact_Code_Quality_Score`, and a disclaimer. Owned by and visible only to
  the creating `User`; references the `Paper` by index identifier; never stores
  external full text or external repository contents.
- **Artifact_Code_Quality_Score**: An LLM-assessed rating (score plus rationale)
  of a `Generation`'s produced code. Lives on the `Generation` only and never
  feeds back into any Paper's `Reproducibility_Score` (`docs/adr/0004`).
- **Reproducibility_Score**: A Paper-level rating, produced by a separate feature
  and **consumed** here only for display; never written by this spec.
- **Upload**: A `Writer`'s persisted manuscript text and optional source code
  (`docs/adr/0003`), used as input for Writer generation.
- **Disclaimer**: The fixed notice attached to every `Generation` and shown with
  every artifact view and download stating that the code is unverified and was
  not executed.

## Requirements

### Requirement 1: Trigger Code Generation (Frontend)

**User Story:** As a User, I want to explicitly trigger code generation for a
Paper, so that I can opt in to producing candidate code when I choose to.

#### Acceptance Criteria

1. WHILE a User is viewing a Paper for which code generation is applicable, THE Codegen_UI SHALL present a generation trigger control that is not activated by default.
2. WHEN a Reader views an indexed Paper whose Index contains no repository link, THE Codegen_UI SHALL offer the Generate case.
3. WHEN a Reader views an indexed Paper whose Index contains a repository link, THE Codegen_UI SHALL offer the Align case.
4. WHEN a Writer views a paper they claim, THE Codegen_UI SHALL offer the Writer generation case.
5. WHEN a User activates the generation trigger, THE Codegen_UI SHALL send a start-generation request to the Codegen_API identifying the Paper and the Case, and SHALL disable the trigger until a response is received or the 30-second request timeout elapses.
6. WHEN the Codegen_API reports that a Generation_Job was started or that an in-flight Job already exists, THE Codegen_UI SHALL present the job status view for that Job.
7. IF no response is received within the 30-second request timeout or the request fails due to a network or server error, THEN THE Codegen_UI SHALL re-enable the trigger and display an error message indicating that generation could not be started.

### Requirement 2: Observe Job Status and Retrieve the Artifact (Frontend)

**User Story:** As a User, I want to watch a generation job's progress and open
its result, so that I can retrieve the generated code once it is ready.

#### Acceptance Criteria

1. WHILE a Generation_Job is pending or running, THE Codegen_UI SHALL poll the Codegen_API for job status and display a progress indicator.
2. WHEN the Codegen_API reports that the Job succeeded, THE Codegen_UI SHALL present the resulting Generation, including a read-only view of each generated file, the Artifact_Code_Quality_Score with its rationale, and the Disclaimer.
3. WHEN the Codegen_API reports that the Job succeeded, THE Codegen_UI SHALL present a control to download the Generation's files as a single archive.
4. WHEN a User downloads a Generation, THE Codegen_UI SHALL include the Disclaimer in the downloaded output.
5. IF the Codegen_API reports that the Job failed, THEN THE Codegen_UI SHALL display an error message and present a control to retry the generation.
6. IF the Codegen_API reports that the Job was refused, THEN THE Codegen_UI SHALL display the reported reason for refusal and SHALL NOT present a retry control for the same unmet precondition.
7. THE Codegen_UI SHALL display the Paper's existing Reproducibility_Score when the Codegen_API provides it, as read-only information, and SHALL NOT present any control that modifies it.

### Requirement 3: Manage Owned Generations (Frontend)

**User Story:** As a User, I want to see and delete the generations I have
created, so that I can manage my own derived artifacts.

#### Acceptance Criteria

1. WHILE a User is authenticated, THE Codegen_UI SHALL display only the Generations owned by that User and SHALL NOT display any Generation owned by another User.
2. WHEN more than one Generation exists for the same (User, Paper, Case), THE Codegen_UI SHALL identify which Generation is the latest.
3. WHEN a User activates the delete control for one of their Generations, THE Codegen_UI SHALL send a delete request to the Codegen_API for that Generation and, on a success response, remove it from the displayed list.
4. IF a delete request fails or no response is received within the 30-second request timeout, THEN THE Codegen_UI SHALL retain the Generation in the list and display an error message indicating that deletion did not complete.

### Requirement 4: Start a Generation Job (Backend)

**User Story:** As the frontend application, I want an endpoint that starts a
generation job, so that generation runs asynchronously without blocking the UI.

#### Acceptance Criteria

1. WHEN the Codegen_API receives a start-generation request from an authenticated User identifying a Paper and a Case for which the preconditions are met, THE Codegen_API SHALL create a Generation_Job owned by that User in a pending state and return a response identifying the Job.
2. IF the Codegen_API receives a start-generation request while an in-flight Generation_Job already exists for the same (User, Paper, Case), THEN THE Codegen_API SHALL NOT create a second Job and SHALL return the existing in-flight Job.
3. IF the Codegen_API receives a start-generation request for the Generate case or the Align case and no Experiment_Setup exists for the Paper, THEN THE Codegen_API SHALL complete the Job in the refused state with a reason indicating that no Experiment_Setup is available, and SHALL NOT call the Generation_Helper.
4. IF the Codegen_API receives a start-generation request for the Align case and the Paper's Index contains no repository link, THEN THE Codegen_API SHALL complete the Job in the refused state with a reason indicating that no repository is available, and SHALL NOT call the Generation_Helper.
5. IF the Codegen_API receives a start-generation request for the Writer generation case and the requesting Writer has no uploaded manuscript for the claimed paper, THEN THE Codegen_API SHALL complete the Job in the refused state with a reason indicating that no upload is available, and SHALL NOT call the Generation_Helper.
6. IF the Codegen_API receives a start-generation request from a request that carries no valid Session, THEN THE Codegen_API SHALL reject the request with an unauthenticated response and SHALL NOT create a Generation_Job.
7. THE Codegen_API SHALL record each Generation_Job with its owning User, Paper index identifier, Case, and current state.

### Requirement 5: Execute the Generation Job (Backend)

**User Story:** As the backend, I want to run a started job through the
generation and scoring helpers, so that a succeeded job yields a persisted,
scored artifact.

#### Acceptance Criteria

1. WHEN a Generation_Job for the Generate case runs, THE Codegen_API SHALL invoke the Generation_Helper with the Paper's Experiment_Setup to produce candidate source files generated from scratch and a README.
2. WHEN a Generation_Job for the Align case runs, THE Codegen_API SHALL invoke the Generation_Helper with the Paper's Experiment_Setup and the Paper's repository link to produce refinement and annotation output aligned to the Experiment_Setup and README, and SHALL NOT store a copy of the external repository contents.
3. WHEN a Generation_Job for the Writer generation case runs and uploaded source code is present, THE Codegen_API SHALL invoke the Generation_Helper to refine the uploaded source to match the uploaded manuscript; and WHEN no uploaded source code is present, THE Codegen_API SHALL invoke the Generation_Helper to generate source from the uploaded manuscript from scratch.
4. WHEN the Generation_Helper returns candidate files, THE Codegen_API SHALL invoke the Scoring_Helper to produce an Artifact_Code_Quality_Score and rationale for those files, and SHALL store the score and rationale on the resulting Generation.
5. WHEN a Generation_Job completes successfully, THE Codegen_API SHALL persist a Generation containing the generated files, the Artifact_Code_Quality_Score with rationale, and the Disclaimer, referencing the Paper by its index identifier, and SHALL set the Job to the succeeded state.
6. WHEN the Codegen_API persists a Generation that supersedes a prior Generation for the same (User, Paper, Case), THE Codegen_API SHALL mark the new Generation as the latest and SHALL retain the superseded Generation until the owning User deletes it.
7. IF the Generation_Helper or the Scoring_Helper reports an error or does not complete, THEN THE Codegen_API SHALL set the Job to the failed state with no Generation persisted.
8. THE Codegen_API SHALL set the Artifact_Code_Quality_Score only on the Generation and SHALL NOT modify the Paper's Reproducibility_Score.

### Requirement 6: Poll, Fetch, Download, and Delete (Backend)

**User Story:** As the frontend application, I want endpoints to read job status
and manage the resulting generation, so that I can present and control a User's
derived artifacts.

#### Acceptance Criteria

1. WHEN the Codegen_API receives a status request for a Generation_Job owned by the authenticated User, THE Codegen_API SHALL return the Job's current state and, when the state is refused, the refusal reason.
2. WHEN the Codegen_API receives a fetch request for a succeeded Job owned by the authenticated User, THE Codegen_API SHALL return the Generation including its files, Artifact_Code_Quality_Score with rationale, and Disclaimer.
3. WHEN the Codegen_API receives a download request for a Generation owned by the authenticated User, THE Codegen_API SHALL return the generated files as a single archive that includes the Disclaimer.
4. WHEN the Codegen_API receives a delete request for a Generation owned by the authenticated User, THE Codegen_API SHALL remove that Generation and return a success response.
5. IF the Codegen_API receives a status, fetch, download, or delete request for a Generation_Job or Generation that is not owned by the authenticated User, THEN THE Codegen_API SHALL respond as though the resource does not exist for that User and SHALL NOT disclose its contents or existence.
6. IF the Codegen_API receives a status, fetch, download, or delete request that carries no valid Session, THEN THE Codegen_API SHALL reject the request with an unauthenticated response.

### Requirement 7: Generation and Scoring Helpers (Business Logic)

**User Story:** As the backend, I want thin, provider-agnostic helpers for
generation and artifact scoring, so that AI calls stay behind a seam I can swap.

#### Acceptance Criteria

1. THE Generation_Helper and the Scoring_Helper SHALL call Amazon Bedrock through the LangChain abstraction and SHALL NOT embed provider credentials in committed source.
2. WHEN the Generation_Helper is asked to produce code and the source material does not determine a target language, THE Generation_Helper SHALL produce the candidate code in Python.
3. WHEN the Generation_Helper produces candidate files, THE Generation_Helper SHALL include a README file describing an overview of the generated code.
4. WHEN the Scoring_Helper assesses a set of candidate files, THE Scoring_Helper SHALL return a numeric Artifact_Code_Quality_Score together with a short rationale.
5. THE Generation_Helper and the Scoring_Helper SHALL NOT execute, run, compile, or otherwise verify the generated code.
6. IF a required Bedrock or AWS configuration value is absent from the environment variables, THEN the helper that requires it SHALL report an error rather than read that value from committed source.

### Requirement 8: Generation Persistence and Schema (Backend)

**User Story:** As a developer of dependent features, I want generation jobs and
artifacts persisted through committed migrations, so that derived artifacts and
their ownership are reliable.

#### Acceptance Criteria

1. THE Codegen_System SHALL introduce the Generation_Job and Generation tables through Alembic migrations committed under `backend/alembic/versions/`, and SHALL NOT create those tables through runtime schema generation (create_all).
2. THE Codegen_API SHALL persist each Generation_Job with a stable identifier, its owning User, the Paper index identifier, the Case, and its state.
3. THE Codegen_API SHALL persist each Generation with a stable identifier, its owning User, the Paper index identifier, the Case, the generated files, the Artifact_Code_Quality_Score with rationale, the Disclaimer, and whether it is the latest for its (User, Paper, Case).
4. THE Codegen_System SHALL enforce, through a constraint, at most one in-flight (pending or running) Generation_Job per (User, Paper, Case).
5. THE Codegen_API SHALL store, for an indexed Paper, only the Paper's index identifier and the derived Generation, and SHALL NOT store the Paper's external full text or the contents of an external repository.
6. WHEN a User deletes a Generation, THE Codegen_API SHALL remove that Generation's record and files and SHALL leave other Generations for the same (User, Paper, Case) unchanged.

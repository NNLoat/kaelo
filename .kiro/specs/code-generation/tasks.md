# Implementation Plan: code-generation

## Overview

This plan implements the `code-generation` feature in dependency order across the
three mandated layers: Business Logic (`Generation_Helper`, `Scoring_Helper`),
Backend persistence + job lifecycle + `Codegen_API`, and Frontend `Codegen_UI`.
Each layer builds on the previous one and ends by wiring the pieces together, so
there is no orphaned code. It depends on the `accounts` spec for the
`current_user` dependency and the `User` table.

- **Backend verification gate:** after every backend task, `cd backend && uv run pytest`
  must pass (pytest + testcontainers against a throwaway `postgres:17`, run on
  the host per `backend/README.md`).
- **Schema:** the `generation_jobs` and `generations` tables are created by an
  Alembic migration committed under `backend/alembic/versions/` and applied via
  `alembic upgrade head` (the container entrypoint) — **never** `create_all`.
  Autogenerate does not emit partial `WHERE` indexes, so the two partial unique
  indexes are added by hand and reviewed.
- **AI calls:** `Generation_Helper`/`Scoring_Helper` are the only Bedrock callers,
  through LangChain (`docs/adr/0002`). **All LLM calls are mocked in tests** —
  never call live Bedrock from the suite.
- **New dependencies:** backend deps via `uv` (`langchain`, `langchain-aws`, and
  `hypothesis` in the dev group); frontend deps (if any) via `pnpm`.
- **Frontend verification:** there is **no automated frontend test gate** — the
  team tests the UI manually. Frontend tasks are verified manually; do not invent
  a frontend test suite.
- Property-based tests use **Hypothesis** (min. 100 iterations each) and are
  tagged with a comment referencing the design property they validate.

## Tasks

- [x] 1. Business logic — `Generation_Helper` + `Scoring_Helper` (`core/codegen.py`)
  - [x] 1.1 Add backend LLM dependencies via uv
    - From `backend/`, run `uv add langchain langchain-aws` so Bedrock access
      through LangChain is available; confirm they land in `pyproject.toml` and
      `uv.lock`. Do not switch package managers.
    - _Requirements: 7.1_

  - [x] 1.2 Extend `Settings` with Bedrock config
    - In `backend/app/core/config.py` add `bedrock_region: str` and
      `bedrock_model_id: str` with **no defaults**, and
      `codegen_job_timeout_seconds: int = 600`.
    - Document `BEDROCK_REGION`, `BEDROCK_MODEL_ID` (and the AWS credential vars)
      in `.env.example` (placeholders only); real values go in `.env`
      (gitignored).
    - _Requirements: 7.6_

  - [x] 1.3 Implement the helpers
    - Create `backend/app/core/codegen.py` with no FastAPI/SQLModel imports.
    - Define `Case` reuse (import from the model or a shared enum), `GenFile`
      (`path`, `content`), `ArtifactScore` (`score`, `rationale`),
      `GenerationInputs` (experiment_setup text, optional repo link, optional
      manuscript text, optional uploaded source), and `GenerationError`.
    - `generate(case, inputs) -> list[GenFile]`: build a case-specific prompt,
      call Bedrock via LangChain (chat model constructed from
      `bedrock_region`/`bedrock_model_id`), parse the response into files. Always
      include a `README`; when the material does not determine a language,
      produce Python. Never execute/compile the output.
    - `score(files) -> ArtifactScore`: ask Bedrock via LangChain to rate the
      files; return a numeric score + short rationale. Never execute the code.
    - Raise `GenerationError` on LLM/parse failure.
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [x] 1.4 Add Hypothesis to the dev dependency group
    - From `backend/`, run `uv add --group dev hypothesis`; confirm it lands in
      the `pyproject.toml` dev group and `uv.lock`.
    - _Requirements: 7.1_

  - [x]* 1.5 Write property test — output always includes a README and defaults to Python
    - Create `backend/tests/test_codegen_helper_properties.py` with the LangChain
      chat model **mocked** to return canned responses.
    - **Property 11: Generated output always includes a README and defaults to Python**
    - **Validates: Requirements 7.2, 7.3**

  - [x]* 1.6 Write example test — helper failure raises `GenerationError`
    - With the mocked model raising / returning unparseable output, assert
      `generate` and `score` surface `GenerationError`.
    - _Requirements: 7.5, 5.7_

- [x] 2. Checkpoint — helpers
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [ ] 3. Data models and migration (`GenerationJob`, `Generation`)
  - [ ] 3.1 Implement the SQLModel tables
    - Create `backend/app/models/generation.py`: `Case` and `JobState` enums;
      `GenerationJob(table=True)` on `generation_jobs` (`id` UUID PK, `owner_id`
      FK→`users.id` indexed, `paper_ref` indexed, `case`, `state` indexed,
      `reason`, `generation_id` FK, `created_at`, `updated_at`);
      `Generation(table=True)` on `generations` (`id` UUID PK, `owner_id` FK,
      `paper_ref`, `case`, `files` JSON of `{path, content}`,
      `code_quality_score`, `code_quality_rationale`, `disclaimer`, `is_latest`
      indexed, `created_at`); plus `JobRead` and `GenerationRead` read schemas.
    - _Requirements: 8.2, 8.3, 8.5_

  - [ ] 3.2 Generate and hand-edit the Alembic migration
    - Generate: `docker compose exec backend uv run alembic revision --autogenerate -m "create generation tables"`.
    - Review the draft so it creates both tables; **add by hand** the two partial
      unique indexes via `op.create_index(..., postgresql_where=...)`: one on
      `(owner_id, paper_ref, case)` WHERE `state IN ('pending','running')`, one on
      `(owner_id, paper_ref, case)` WHERE `is_latest`. Commit under
      `backend/alembic/versions/`. Applied via `alembic upgrade head`, never
      `create_all`.
    - _Requirements: 8.1, 8.4, 5.6_

  - [ ]* 3.3 Write migration smoke test
    - Extend `backend/tests/test_migrations.py` with an upgrade → downgrade →
      upgrade run asserting both tables and both partial unique indexes exist
      after upgrade (single run, not PBT).
    - _Requirements: 8.1_

  - [ ]* 3.4 Write config smoke test
    - Assert constructing `Settings` without `BEDROCK_REGION`/`BEDROCK_MODEL_ID`
      in the environment raises at startup (no committed default).
    - _Requirements: 7.6_

- [ ] 4. Checkpoint — models, migration
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [ ] 5. Job lifecycle + `Codegen_API` router (backend)
  - [ ] 5.1 Implement input loaders and the worker
    - In `backend/app/routers/codegen.py` (or a small `app/core/codegen_jobs.py`),
      implement `run_job(job_id)` with its own DB session: set `running`; load
      `GenerationInputs` for the case (consume the existing `Experiment_Setup`,
      the Paper index repo link, or the Writer `Upload`); call
      `generate` then `score`; persist a `Generation` and flip the prior latest
      for `(owner, paper_ref, case)` to `is_latest=false`; set the job
      `succeeded` with `generation_id`. On any helper error set `failed`, persist
      no `Generation`. Never write a Paper's `Reproducibility_Score`.
    - Treat a `running` job older than `codegen_job_timeout_seconds` as `failed`
      on read.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

  - [ ] 5.2 Implement the start endpoint and precondition checks
    - `POST /jobs` using `current_user` + `get_session`: return the existing
      in-flight job for `(user, paper_ref, case)` if any (catch `IntegrityError`
      from the partial unique index, roll back, re-select, return the winner);
      else evaluate preconditions — generate/align need an `Experiment_Setup`,
      align needs a repo link, writer needs an uploaded manuscript — persisting
      `refused` with a reason when unmet (helper never called); else INSERT
      `pending`, schedule `run_job` via `BackgroundTasks`, return `202`.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ] 5.3 Implement poll / fetch / download / delete / list endpoints
    - `GET /jobs/{id}` → `JobRead` (owner-scoped, `404` otherwise); refusal reason
      included. `GET /generations/{id}` → `GenerationRead`.
      `GET /generations/{id}/archive` → `application/zip` including a top-level
      `DISCLAIMER.txt`. `GET /generations` → caller's generations, newest first.
      `DELETE /generations/{id}` → `204`, removing only that row. All owner-scoped
      with `404` for not-owned/absent; `401` without a session.
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 3.1, 8.6_

  - [ ] 5.4 Register the codegen router in `main.py`
    - Add `app.include_router(codegen.router)` in `backend/app/main.py`; leave
      existing routes untouched. This wires the backend together.
    - _Requirements: 4.1, 6.1_

  - [ ]* 5.5 Write property test — at most one in-flight job per (user, paper, case)
    - Create `backend/tests/test_codegen_api_properties.py` driving endpoints via
      `TestClient` against the testcontainer DB with the helper **mocked**.
    - **Property 1: At most one in-flight job per (user, paper, case)**
    - **Validates: Requirements 4.2, 8.4**

  - [ ]* 5.6 Write property test — unmet preconditions refuse without calling the helper
    - **Property 2: Unmet preconditions refuse without calling the helper**
    - **Validates: Requirements 4.3, 4.4, 4.5**

  - [ ]* 5.7 Write property test — a succeeded job yields exactly one latest, scored Generation
    - Invoke `run_job` with a mocked helper returning files.
    - **Property 3: A succeeded job yields exactly one latest, scored Generation**
    - **Validates: Requirements 5.1, 5.4, 5.5, 5.6**

  - [ ]* 5.8 Write property test — helper failure fails the job and persists no artifact
    - **Property 4: Helper failure fails the job and persists no artifact**
    - **Validates: Requirements 5.7**

  - [ ]* 5.9 Write property test — generation never writes a Paper's Reproducibility Score
    - **Property 5: Generation never writes a Paper's Reproducibility Score**
    - **Validates: Requirements 5.8 (ADR-0004)**

  - [ ]* 5.10 Write property test — owner scoping and unauthenticated requests
    - **Property 6: Owner scoping — cross-user access is indistinguishable from absent**
    - **Property 7: Unauthenticated requests never act**
    - **Validates: Requirements 6.5, 4.6, 6.6**

  - [ ]* 5.11 Write property tests — supersede/retain and targeted delete
    - **Property 8: Re-run supersedes but retains the prior Generation**
    - **Property 9: Delete removes only the targeted Generation**
    - **Property 10: Stored artifacts contain only derived text**
    - **Validates: Requirements 5.6, 6.4, 8.5, 8.6**

  - [ ]* 5.12 Write example/edge tests for endpoints
    - Create `backend/tests/test_codegen_api.py`: R4.2 race (two near-simultaneous
      starts → one in-flight, loser returns winner); R2.6/R4.3 generate with no
      `Experiment_Setup` → `refused` + reason, helper not called; R6.3 archive of
      an owned succeeded generation contains every file plus `DISCLAIMER.txt`;
      R6.5 cross-user access → `404`; happy-path smoke per case with a mocked
      helper.
    - _Requirements: 4.2, 4.3, 6.3, 6.5_

- [ ] 6. Checkpoint — backend Codegen_API
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [x] 7. Frontend — `Codegen_UI` (manual verification; no automated test gate)
  - [x] 7.1 Add any required frontend dependencies via pnpm
    - If the UI needs packages beyond the existing stack (e.g. a client-side zip
      helper is **not** needed — the archive comes from the API), add them from
      `frontend/` with `pnpm add <pkg>` (pinned). If none are needed, note that
      and skip. Do not switch package managers.
    - None needed: existing React/TS/Tailwind + `fetch` covers it; the archive
      download uses a Blob + anchor, no zip library. Skipped.
    - _Requirements: 1.1, 2.1, 3.1_

  - [x] 7.2 Implement the typed API client `api/codegen.ts`
    - Create `frontend/src/api/codegen.ts` with `Case`, `JobState`, `JobRead`,
      `GenFile`, `GenerationRead` types and `startJob`, `getJob`,
      `getGeneration`, `downloadArchive`, `listGenerations`, `deleteGeneration`.
    - Every call uses `credentials: "include"` and a per-request
      `AbortController` for the 30s timeout.
    - _Requirements: 1.5, 1.7, 2.1, 3.3, 3.4_

  - [x] 7.3 Implement `GenerateButton`
    - Create `frontend/src/components/GenerateButton.tsx`: the per-action opt-in
      trigger, never pre-activated; parent passes the resolved `Case` (Reader+no
      repo → generate, Reader+repo → align, Writer → writer) and label
      (**Generate code** / **Align code** / **Generate from upload**); on
      activate call `startJob`, disable until response/30s, hand off to the status
      view on success, show a start-failed message on timeout/network/5xx.
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [x] 7.4 Implement `JobStatusView` with polling
    - Create `frontend/src/components/JobStatusView.tsx`: poll `getJob` while
      `pending`/`running` (interval with backoff cap) showing a calm inline
      progress line; on `succeeded` load and render the `Generation`; on `failed`
      show an error + **Try again** (restart the job); on `refused` show the
      server reason and no retry for the same precondition.
    - _Requirements: 2.1, 2.5, 2.6_

  - [x] 7.5 Implement `ArtifactView`
    - Create `frontend/src/components/ArtifactView.tsx`: two-pane read-only view
      (file-tree rail + viewer), the `Artifact_Code_Quality_Score` + rationale,
      the persistent amber `Disclaimer` band, and a **Download code** control
      calling `downloadArchive`. When the parent supplies the Paper's
      `Reproducibility_Score`, show it read-only with no mutating control.
    - _Requirements: 2.2, 2.3, 2.4, 2.7_

  - [x] 7.6 Implement `GenerationsList`
    - Create `frontend/src/components/GenerationsList.tsx`: list only the current
      User's generations (newest first), mark the latest per `(paper, case)`,
      offer **Delete** per item; on success remove the row, on timeout/error keep
      it and show a deletion-failed message.
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 7.7 Wire `Codegen_UI` into the app
    - Mount the generation trigger on the Paper/Writer view and route into
      `JobStatusView` → `ArtifactView`; surface `GenerationsList` for the signed-in
      User. Follow the visual direction in `design.md` (teal `signal` accent,
      amber `caution` reserved for the disclaimer and refused/failed states). This
      integrates the frontend end-to-end.
    - _Requirements: 1.1, 2.2, 3.1_

- [ ] 8. Final checkpoint
  - Backend: ensure all tests pass (`cd backend && uv run pytest`). Frontend:
    manually verify, per case, trigger → status polling → artifact view with
    disclaimer → download → delete. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; they
  are all tests. The core generation flow (unmarked tasks) is required.
- **All LLM calls are mocked in tests.** No test calls live Bedrock.
- Each task references specific requirements and/or design Property numbers for
  traceability.
- Backend gate: `cd backend && uv run pytest` (pytest + testcontainers, run on
  the host). Property tests use Hypothesis at ≥100 iterations.
- Schema is created by a committed Alembic migration under
  `backend/alembic/versions/` and applied via `alembic upgrade head` — never
  `create_all`. The two partial unique indexes are hand-added (autogenerate omits
  `WHERE` clauses).
- Frontend has no automated test gate; verify UI manually.
- This spec consumes the `Experiment_Setup` and Paper-level `Reproducibility_Score`
  as existing inputs; it neither extracts nor computes them.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "3.1", "7.1"] },
    { "id": 1, "tasks": ["1.3", "1.4", "3.2", "7.2"] },
    { "id": 2, "tasks": ["1.5", "1.6", "3.3", "3.4", "5.1", "7.3"] },
    { "id": 3, "tasks": ["5.2", "5.3", "7.4", "7.5", "7.6"] },
    { "id": 4, "tasks": ["5.4", "7.7"] },
    { "id": 5, "tasks": ["5.5", "5.6", "5.7", "5.8", "5.9", "5.10", "5.11", "5.12"] }
  ]
}
```

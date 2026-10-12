# Implementation Plan: reproducibility-scoring

## Overview

This plan implements the `reproducibility-scoring` feature in dependency order
across the two mandated layers: Business Logic (`Score_Engine`, the pure
computation) and Backend (persistence + migration, the two external
integrations, the async job, and the `Scoring_API`). The pure engine comes
first so the number can be computed and property-tested before any I/O is wired;
the backend then gathers signals, calls the engine, and exposes the endpoints.
There is **no frontend concern** in this spec — the score-display UI belongs to
`paper-search`.

- **Backend verification gate:** after every backend task, `cd backend && uv run pytest`
  must pass (pytest + testcontainers against a throwaway `postgres:17`, run on
  the host per `backend/README.md`).
- **Schema:** the `reproducibility_score` and `experiment_setup` tables are
  created by an Alembic migration committed under `backend/alembic/versions/`
  and applied via `alembic upgrade head` (the container entrypoint) — **never**
  `create_all`.
- **New dependencies:** backend deps are added via `uv` (`langchain` +
  `langchain-aws` for Bedrock, an HTTP client for the GitHub API, and
  `hypothesis` in the dev group). No new frontend deps.
- **`Paper` dependency:** this spec reads a minimal `Paper` (`id`, optional
  `repo_url`) introduced by `paper-search`. Where `paper-search` has not landed,
  the migration here contributes the columns this spec reads (see design,
  "Dependency on paper-search / Paper").
- Property-based tests use **Hypothesis** (min. 100 iterations each) and are
  tagged with a comment referencing the design property they validate.

## Tasks

- [ ] 1. Business logic — `Score_Engine` (`core/scoring.py`)
  - [ ] 1.1 Implement the `Score_Engine` pure module
    - Create `backend/app/core/scoring.py` with no FastAPI/SQLModel/network
      imports. Define `SignalStatus`, `SignalKind`, `SignalInput`,
      `SignalBreakdown`, `ScoreResult`, `NoScoreAvailable`, and the
      `SETUP_CHECKLIST` (`hyperparameters`, `datasets`, `environment`,
      `hardware`, `procedure`).
    - `compute_score(signals, weights)`: deterministic weighted blend;
      renormalize weights over `OK` signals (Partial Score); return
      `score` (0..1), `display` (0..100), `band`, and the per-signal breakdown;
      raise `NoScoreAvailable` when every signal is `UNAVAILABLE`.
    - `repo_quality_value(readme, license_, tests, recent, weights)`: weighted
      sum of the four independent sub-signals → 0..1.
    - `setup_completeness_value(present_fields)`: `len(present) / len(SETUP_CHECKLIST)`.
    - Derive `display`/`band` from configured thresholds (passed in, not read
      from env here — the engine stays pure).
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 8.1, 8.4, 8.5, 8.6_

  - [ ] 1.2 Add Hypothesis to the dev dependency group
    - From `backend/`, run `uv add --group dev hypothesis`; confirm it lands in
      `pyproject.toml` dev group and `uv.lock`.
    - _Requirements: 3.1_

  - [ ]* 1.3 Write property test — score is always in range
    - Create `backend/tests/test_scoring_properties.py`.
    - **Property 1: Score is always in range**
    - **Validates: Requirements 3.1, 3.6**

  - [ ]* 1.4 Write property test — determinism
    - **Property 2: Determinism**
    - **Validates: Requirements 3.3, 8.4**

  - [ ]* 1.5 Write property test — Partial Score renormalizes over available signals
    - **Property 3: Partial Score renormalizes over available signals**
    - **Validates: Requirements 3.4, 2.4, 8.5**

  - [ ]* 1.6 Write property test — all-unavailable yields no score
    - **Property 4: All-unavailable yields no score**
    - **Validates: Requirements 3.5, 6.3**

  - [ ]* 1.7 Write property test — monotonicity in each signal
    - **Property 5: Monotonicity in each signal**
    - **Validates: Requirements 3.2, 8.1**

  - [ ]* 1.8 Write property test — setup completeness is the present-fraction
    - **Property 6: Setup completeness is the present-fraction**
    - **Validates: Requirements 3.8**

  - [ ]* 1.9 Write property test — repo-quality sub-signals are independent
    - **Property 7: Repo-quality sub-signals are independent**
    - **Validates: Requirements 3.7**

- [ ] 2. Checkpoint — Score_Engine
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [ ] 3. Data models, configuration, and migration
  - [ ] 3.1 Implement the scoring SQLModels
    - Create `backend/app/models/scoring.py`: `ScoreStatus` enum
      (`none`/`pending`/`ready`/`failed`), `ReproducibilityScore(table=True)` on
      `reproducibility_score` (`paper_id` FK + unique, `status`, `score`,
      `display`, `band`, `breakdown` JSON, `explanation`, `reason`,
      `updated_at`), and `ExperimentSetup(table=True)` on `experiment_setup`
      (`paper_id` FK + unique, `fields` JSON, `present_fields` JSON,
      `updated_at`).
    - If `paper-search` has not introduced `Paper`, add a minimal
      `backend/app/models/paper.py` with `id` and optional `repo_url` so the FKs
      resolve (coordinate with `paper-search` to avoid a duplicate table).
    - _Requirements: 7.2, 7.3, 7.4_

  - [ ] 3.2 Extend `Settings` with scoring config
    - In `backend/app/core/config.py` add signal weights
      (`repro_weight_repo_existence/_repo_quality/_setup_completeness`),
      repo-quality sub-weights, band thresholds
      (`repro_band_strong`/`_moderate`), `github_token: str | None = None`, and
      `bedrock_region`/`bedrock_model_id` with **no default**.
    - Document the new env vars (`GITHUB_TOKEN`, `BEDROCK_REGION`,
      `BEDROCK_MODEL_ID`, AWS credentials) in `.env.example` (placeholders only)
      and set real values in `.env` (gitignored).
    - _Requirements: 3.2, 7.5, 4.2, 5.6_

  - [ ] 3.3 Generate and review the Alembic migration for the scoring tables
    - Generate: `docker compose exec backend uv run alembic revision --autogenerate -m "create scoring tables"`.
    - Review the draft so it creates `reproducibility_score` and
      `experiment_setup` with their **unique `paper_id` indexes** and FKs (and
      `paper.repo_url` if contributed here); commit under
      `backend/alembic/versions/`. Applied via `alembic upgrade head`, **not**
      `create_all`.
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ]* 3.4 Write migration smoke test
    - Extend `backend/tests/test_migrations.py` with an upgrade → downgrade →
      upgrade run asserting the `reproducibility_score` and `experiment_setup`
      tables and their unique `paper_id` indexes exist after upgrade.
    - _Requirements: 7.1_

  - [ ]* 3.5 Write config smoke test
    - Assert constructing `Settings` without `BEDROCK_REGION` / `BEDROCK_MODEL_ID`
      in the environment raises at startup (no committed default).
    - _Requirements: 7.5_

- [ ] 4. Checkpoint — models, config, migration
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [ ] 5. Backend services — `Repo_Inspector` and `Setup_Extractor`
  - [ ] 5.1 Add the GitHub HTTP client and Bedrock/LangChain deps via uv
    - From `backend/`, run `uv add httpx` (if not already present) and
      `uv add langchain langchain-aws`; confirm `pyproject.toml` and `uv.lock`.
    - _Requirements: 4.1, 5.1, 5.6_

  - [ ] 5.2 Implement `Repo_Inspector` (`services/repo_inspector.py`)
    - Create `backend/app/services/repo_inspector.py` with `RepoQuality` and
      `inspect(repo_url)`: no URL → `exists=False`, `status=OK`, min
      contribution; non-GitHub host → `exists=True`, host-specific sub-signals
      `UNAVAILABLE`; GitHub → query README/license/tests/recent-activity, auth
      with `GITHUB_TOKEN` when present; HTTP error / timeout / rate-limit `403`
      → `status=UNAVAILABLE`. Read metadata only — never clone or persist file
      contents.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ] 5.3 Implement `Setup_Extractor` (`services/setup_extractor.py`)
    - Create `backend/app/services/setup_extractor.py` with `ExtractedSetup`,
      `extract(material)` (Bedrock via LangChain extracts the checklist fields,
      marks each present/absent; failure/timeout/unparseable → `status=UNAVAILABLE`),
      and `explain(score, setup)` (human-readable text whose only interpolated
      number is `score.display`; post-check rejects any other numeric token).
    - Persist only the derived setup; read Bedrock/AWS creds from `Settings`.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 8.6_

  - [ ]* 5.4 Write example tests for the services (network stubbed)
    - Create `backend/tests/test_scoring_services.py`: `Repo_Inspector` with a
      non-GitHub URL (4.3) and no URL (4.4); GitHub + Bedrock failures →
      `UNAVAILABLE` (4.5, 5.4), all with HTTP/LLM calls monkeypatched.
    - _Requirements: 4.3, 4.4, 4.5, 5.4_

  - [ ]* 5.5 Write property test — explanation never contradicts the number
    - **Property 11: Explanation never contradicts the number**
    - **Validates: Requirements 5.3, 8.6**

- [ ] 6. Checkpoint — backend services
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [ ] 7. Async job and `Scoring_API` router (backend)
  - [ ] 7.1 Implement the background scoring job
    - In `backend/app/routers/scoring.py` (or a small `services/scoring_job.py`),
      implement `run_scoring(paper_id)`: open its own DB `Session`; gather
      signals via `Repo_Inspector` + `Setup_Extractor`; call
      `Score_Engine.compute_score`; on `NoScoreAvailable` set
      `status=failed`+reason; else call `explain`, persist score + breakdown +
      setup + explanation, set `status=ready`. Wrap the body so any unexpected
      error sets `failed` (never leaves `pending`). Re-score upserts on
      `paper_id` (no duplicate rows).
    - _Requirements: 6.1, 6.2, 6.3, 6.6, 7.4_

  - [ ] 7.2 Implement the `Scoring_API` endpoints
    - Create/extend `backend/app/routers/scoring.py` with
      `APIRouter(prefix="/api")` using the existing `get_session` dependency.
    - `POST /papers/{paper_id}/score`: `404` if the Paper is missing; `pending`
      already → return it, no duplicate job; `ready` + no `?recompute=true` →
      return existing score; otherwise set `pending`, schedule `run_scoring`
      via `BackgroundTasks`, return `202 {status: pending}`. Accept any
      Session-identified Reader or Writer.
    - `GET /papers/{paper_id}/score`: map `score_status` to
      `none`/`pending`/`failed`/`ready`, returning score, display, band,
      breakdown (contribution + weight + status per signal), and explanation when
      `ready`.
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ] 7.3 Register the scoring router in `main.py`
    - Add `app.include_router(scoring.router)` in `backend/app/main.py`; leave
      existing routes untouched. This wires the backend together.
    - _Requirements: 1.1, 2.1_

  - [ ]* 7.4 Write property test — trigger is idempotent while pending
    - Create `backend/tests/test_scoring_api_properties.py` driving endpoints via
      `TestClient` against the testcontainer DB, with the two services
      monkeypatched to return canned signals.
    - **Property 8: Trigger is idempotent while pending**
    - **Validates: Requirements 1.3**

  - [ ]* 7.5 Write property test — status transitions never strand a Paper in pending
    - **Property 9: Status transitions never strand a Paper in pending**
    - **Validates: Requirements 6.2, 6.3, 6.6**

  - [ ]* 7.6 Write property test — read reflects persisted status exactly
    - **Property 10: Read reflects persisted status exactly**
    - **Validates: Requirements 2.1, 2.3, 2.5, 2.6**

  - [ ]* 7.7 Write example/integration tests for the end-to-end flow
    - Create `backend/tests/test_scoring_api.py`: trigger on a missing Paper →
      `404` (1.2); trigger `ready` with/without `?recompute=true` (1.4, 1.5);
      all-signals-unavailable → `failed` (3.5, 6.3); end-to-end trigger→job→read
      landing in `ready` with a persisted breakdown + explanation (6.1, 6.2);
      an injected unexpected error landing in `failed` not `pending` (6.6);
      re-score leaves exactly one score + one setup row (7.4).
    - _Requirements: 1.2, 1.4, 1.5, 3.5, 6.1, 6.2, 6.3, 6.6, 7.4_

- [ ] 8. Final checkpoint
  - Backend: ensure all tests pass (`cd backend && uv run pytest`). Confirm the
    design-level reliability guarantees hold end-to-end: identical signal inputs
    produce an identical number (R8.4), Partial Scores mark skipped signals
    (R8.5), and the LLM never changes the number (R8.6). Ask the user if
    questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; they
  are all tests. The core scoring flow (unmarked tasks) is required.
- Requirement 8 (score design, Reader/Writer benefit, reliability) is a
  design-level requirement: it is satisfied by the determinism of `Score_Engine`
  (1.1), the config-driven weights/thresholds (3.2), the breakdown surfaced by
  the read endpoint (7.2), and the bounded LLM role (5.3). Its guarantees are
  re-confirmed at the final checkpoint (task 8).
- Each task references specific requirements and/or design Property numbers for
  traceability.
- Backend gate: `cd backend && uv run pytest` (pytest + testcontainers, run on
  the host). Property tests use Hypothesis at ≥100 iterations.
- Schema is created by a committed Alembic migration under
  `backend/alembic/versions/` and applied via `alembic upgrade head` — never
  `create_all` (that exists only for test speed).
- External integrations (`Repo_Inspector`, `Setup_Extractor`) are tested with the
  network/LLM stubbed; no live GitHub or Bedrock calls in the test suite.
- This spec depends on `paper-search` for the `Paper`; coordinate the `Paper`
  table ownership so the two specs do not define it twice.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "3.1", "3.2"] },
    { "id": 1, "tasks": ["1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "3.3", "5.1"] },
    { "id": 2, "tasks": ["3.4", "3.5", "5.2", "5.3"] },
    { "id": 3, "tasks": ["5.4", "5.5", "7.1"] },
    { "id": 4, "tasks": ["7.2"] },
    { "id": 5, "tasks": ["7.3"] },
    { "id": 6, "tasks": ["7.4", "7.5", "7.6", "7.7"] }
  ]
}
```

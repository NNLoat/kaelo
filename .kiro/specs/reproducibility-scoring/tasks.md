# Implementation Plan: reproducibility-scoring

## Overview

This plan implements `reproducibility-scoring` in dependency order across the
three mandated layers: Business Logic (`services/repro/`: inspector, scorers,
LLM extractor/explainer), Backend (the `score_reproducibility` seam that
replaces the `paper-search` stub, plus `ReproducibilityScore`/`ExperimentSetup`
persistence), and Frontend (populate the detail-view breakdown + Experiment
Setup + explanation). Each layer builds on the previous one and ends by wiring
the pieces together, so there is no orphaned code.

- **This feature unstubs `paper-search`.** It replaces the body of
  `backend/app/services/reproducibility.py` (the `paper-search` stub) at the
  **same signature** `score_reproducibility(paper_id: int) -> float`, preserving
  the Score_Status contract so the paper-search orchestrator needs no change.
- **The number is rule-based.** `code_quality.py`, `completeness.py`, and
  `scorer.py` are pure functions with **no LLM import**. The LLM
  (`extractor.py`, `explainer.py`) only produces the structured Experiment Setup
  and a prose explanation; it never produces or alters a score.
- **GitHub-only, token is a secret.** `Repo_Inspector` supports GitHub via the
  REST API behind a `RepoHost` interface. `GITHUB_TOKEN` is read from env only,
  sent only to the GitHub API over HTTPS in the `Authorization` header, and
  **never** logged, persisted, returned in any API response, surfaced to the
  frontend, or placed in an LLM prompt. A non-HTTPS `github_api_base` is rejected
  at startup.
- **experiment_setup alignment (agreed with paper-search).** The normalized
  `experiment_setups` table is the source of truth; every run also **mirrors**
  the setup into the existing `papers.experiment_setup` JSON column as
  `{hyperparameters, datasets, environment, available}` in the same transaction,
  so paper-search's detail read path is unchanged. The reproducibility
  **breakdown** is served via an additive, nullable `reproducibility_breakdown`
  field added to `GET /api/papers/{id}`.
- **Backend verification gate:** after every backend task, `cd backend && uv run pytest`
  must pass (pytest + testcontainers against a throwaway `postgres:17`, run on
  the host). GitHub and the LLM are **mocked/faked in tests** — never called for
  real — so tests stay deterministic and offline.
- **Schema:** `reproducibility_scores` and `experiment_setups` are created by an
  Alembic migration committed under `backend/alembic/versions/` and applied via
  `alembic upgrade head` — never `create_all`.
- **New dependencies:** reuse `httpx`, `langchain`/`langchain-aws`, and
  `hypothesis` added by earlier specs; add nothing new unless required.
- **Frontend verification:** no automated frontend test gate — the team tests the
  UI manually. Do not invent a frontend test suite.
- Property-based tests use **Hypothesis** (min. 100 iterations each) and are
  tagged with a comment referencing the design property they validate.

## Tasks

- [x] 1. Business logic — rule-based scorers (pure, no LLM)
  - [x] 1.1 Define the shared signal/data shapes
    - Create `backend/app/services/repro/__init__.py` and
      `backend/app/services/repro/types.py` with the `RepoSignals` dataclass
      (`exists`, `has_readme`, `has_license`, `has_tests`, `recent_activity`,
      `inspectable`, `failed`), the `ExperimentSetupData` dataclass
      (`hyperparameters`/`datasets`/`environment`, each `str | None`), and a
      `ReproducibilityUnavailable` exception.
    - _Requirements: 1.2, 3.1, 4.4_

  - [x] 1.2 Implement `Code_Quality_Scorer` (`repro/code_quality.py`)
    - `code_quality(signals) -> float`: repo absent/not inspectable → `0.0`
      (R2.2); else a deterministic weighted, normalized `[0,1]` score over
      `{readme, license, tests, recent_activity}`, non-decreasing in each positive
      signal (R2.1). No LLM import.
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 1.3 Implement `Setup_Completeness` (`repro/completeness.py`)
    - `completeness(setup) -> float`: `None`/unavailable → `0.0`; else
      populated-field fraction over `(hyperparameters, datasets, environment)`
      (R4.1). No LLM import.
    - _Requirements: 4.1_

  - [x] 1.4 Implement `Reproducibility_Scorer` (`repro/scorer.py`)
    - `reproducibility(code_quality, repo_exists, setup_completeness, *, w_repo, w_setup) -> float`:
      deterministic blend in `[0,1]`, non-decreasing in `code_quality` and
      `setup_completeness`, weights from config (R4.2, R4.6); a non-inspectable
      repo still scores from the setup contribution (R4.3). No LLM import.
    - _Requirements: 4.2, 4.3, 4.5, 4.6_

  - [x]* 1.5 Write property test — code-quality deterministic + monotonic
    - Create `backend/tests/test_repro_scorers_properties.py`.
    - **Property 1: Code-Quality Score is deterministic and monotonic in positive signals**
    - **Validates: Requirements 2.1, 2.4**

  - [x]* 1.6 Write property test — repo-absent yields minimum code-quality
    - **Property 2: Repository-absent yields the minimum code-quality score**
    - **Validates: Requirements 2.2**

  - [x]* 1.7 Write property test — setup completeness = populated fraction
    - **Property 3: Setup completeness equals the populated-field fraction**
    - **Validates: Requirements 4.1**

  - [x]* 1.8 Write property test — reproducibility deterministic, in range, monotonic
    - **Property 4: Reproducibility Score is deterministic, in range, and monotonic**
    - **Validates: Requirements 4.2, 4.6**

  - [x]* 1.9 Write property test — no repo but a setup is still scored
    - **Property 5: A paper with no repo but a setup is still scored**
    - **Validates: Requirements 4.3**

- [x] 2. Checkpoint — rule-based scorers
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [x] 3. Business logic — GitHub inspector and LLM extractor/explainer (external — mocked in tests)
  - [x] 3.1 Implement the `RepoHost` interface and `GitHubRepoHost` (`repro/inspector.py`)
    - Define a `RepoHost` Protocol (`inspect(repo_url, *, timeout) -> RepoSignals`)
      and `inspect_repo(repo_url | None) -> RepoSignals` that returns
      not-inspectable for absent/malformed/non-GitHub URLs (R1.3).
    - `GitHubRepoHost`: parse owner/repo from a github.com URL; call
      `GET /repos/{o}/{r}` (existence, `pushed_at` → recent activity vs
      `repo_recency_days`, license), `GET /repos/{o}/{r}/readme`, and a tests
      heuristic via the contents/trees API. Clean `404` → `exists=false,
      inspectable=true`; API error/timeout/`403`/`429` rate-limit → `failed=true`
      (R1.1, R1.4). Never clone; metadata only (R1.5).
    - **Token security:** send `GITHUB_TOKEN` only in the `Authorization` header
      over HTTPS; configure the HTTP client so the header is never logged;
      validate `github_api_base` is HTTPS. Token never persisted/returned/prompted.
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x] 3.2 Implement `Setup_Extractor` (`repro/extractor.py`, Bedrock via LangChain)
    - `extract_setup(title, abstract) -> ExperimentSetupData`: extract from
      Reader-side index material only (R3.1, R3.4); each field absent when
      unsupported, never fabricated (R3.2); raise on failure/timeout so the seam
      records the setup unavailable (R3.3); model/creds from env (R3.5). No ranking
      or scoring logic.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.3 Implement `Score_Explainer` (`repro/explainer.py`, Bedrock via LangChain)
    - `explain(score, signals, completeness) -> str`: short prose referencing the
      signals (R5.1); `score` is a fixed input, never recomputed (R5.2); the
      prompt and output are built from paper metadata + computed signals only and
      are scrubbed of any token. The caller proceeds without an explanation on
      failure (R5.3).
    - _Requirements: 5.1, 5.2, 5.3_

  - [x]* 3.4 Write example/edge tests — inspection outcomes + LLM failure handling
    - Create `backend/tests/test_repro_inspector.py` with a faked GitHub `RepoHost`
      / mocked `httpx`: assert `404` → `exists=false, inspectable=true`; timeout /
      `403` rate-limit → `failed=true`; non-GitHub/malformed URL →
      `inspectable=false`. Assert `extract_setup` raises on a mocked LLM error and
      `explain` failure is swallowed (LLM mocked — never called for real).
    - _Requirements: 1.1, 1.3, 1.4, 3.3, 5.3_

  - [x]* 3.5 Write property test — inspection distinguishes absent from failed
    - **Property 9: Inspection distinguishes "signal absent" from "inspection failed"**
    - **Validates: Requirements 1.1, 1.4**

  - [x]* 3.6 Write property test — non-GitHub/malformed URLs not inspectable
    - **Property 10: Non-GitHub or malformed repo URLs are not inspectable**
    - **Validates: Requirements 1.3**

- [x] 4. Checkpoint — inspector and LLM
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [x] 5. Data model, configuration, and migration
  - [x] 5.1 Implement the `ReproducibilityScore` and `ExperimentSetup` models
    - Create `backend/app/models/reproducibility.py` reusing `ScoreStatus` from
      `app.models.paper`: `ReproducibilityScore` on `reproducibility_scores`
      (`paper_id` FK→papers.id unique+indexed; `score`/`status`;
      `code_quality_score`, `repo_exists`, `repo_inspectable`,
      `setup_completeness`; nullable `explanation`; `created_at`/`updated_at`) and
      `ExperimentSetup` on `experiment_setups` (`paper_id` FK unique+indexed;
      `hyperparameters`/`datasets`/`environment` nullable; `available` bool;
      timestamps).
    - Register both in `app/models/__init__.py` for `SQLModel.metadata` and
      Alembic autogenerate.
    - _Requirements: 7.1, 7.2, 7.4_

  - [x] 5.2 Extend `Settings` with GitHub + reproducibility config
    - In `backend/app/core/config.py` add `github_api_base` (default
      `https://api.github.com`, validated HTTPS), `github_token: str | None = None`
      (secret; env only, no real default), `repo_recency_days: int = 365`,
      `repo_inspect_timeout_seconds: float = 10.0`, `repro_repo_weight: float = 0.5`,
      `repro_setup_weight: float = 0.5`. Reuse the Bedrock settings from
      paper-search.
    - Document `GITHUB_TOKEN` and `GITHUB_API_BASE` in `.env.example`
      (placeholder only); real token in `.env` (gitignored). Reject a non-HTTPS
      `github_api_base` at startup.
    - _Requirements: 1.6, 3.5, 7.6_

  - [x] 5.3 Generate and review the Alembic migration
    - Generate: `docker compose exec backend uv run alembic revision --autogenerate -m "create reproducibility tables"`.
    - Review so it creates `reproducibility_scores` and `experiment_setups` with
      the unique `paper_id` FKs/indexes; commit under
      `backend/alembic/versions/`. Applied by `alembic upgrade head`, never
      `create_all`.
    - _Requirements: 7.3_

  - [x]* 5.4 Write migration smoke test
    - Extend `backend/tests/test_migrations.py` asserting both new tables and
      their unique `paper_id` indexes exist after upgrade → downgrade → upgrade.
    - _Requirements: 7.3_

  - [x]* 5.5 Write config smoke test
    - Assert a non-HTTPS `github_api_base` is rejected at startup; assert the
      Bedrock-missing startup failure still holds (inherited from paper-search).
    - _Requirements: 1.6, 7.6_

- [x] 6. Checkpoint — model, config, migration
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [x] 7. Backend — the `score_reproducibility` seam (unstub paper-search)
  - [x] 7.1 Implement the seam pipeline (`services/reproducibility.py`)
    - Replace the paper-search stub body, keeping the signature
      `score_reproducibility(paper_id: int) -> float`. Open an own `Session`; load
      the `Paper` (`repo_url`, `title`, `abstract`); run inspect → code_quality,
      extract → completeness, then `reproducibility(...)`; call `explain(...)`
      (swallow failure). Raise `ReproducibilityUnavailable` only when the repo is
      not inspectable **and** the setup is unavailable (R4.4, R6.4).
    - _Requirements: 6.2, 6.3, 6.4, 6.7, 4.3, 4.4_

  - [x] 7.2 Persist results and mirror onto the Paper (same transaction)
    - Upsert the `ReproducibilityScore` row (score, status, code-quality,
      repo_exists, repo_inspectable, setup_completeness, explanation) and the
      `ExperimentSetup` row (fields + `available`) by `paper_id` — update, don't
      duplicate (R7.4). In the **same transaction**, mirror the setup into
      `papers.experiment_setup` as `{hyperparameters, datasets, environment,
      available}` and write `papers.reproducibility_score` /
      `reproducibility_status` (`ready`/`unavailable`) so the paper-search
      orchestrator recomputes the Final Score (R6.3, R6.6, R7.1, R7.2, R7.5).
    - _Requirements: 6.3, 6.6, 7.1, 7.2, 7.4, 7.5_

  - [x] 7.3 Extend the paper detail response with `reproducibility_breakdown`
    - In `backend/app/routers/papers.py` (paper-search), add the additive,
      nullable `reproducibility_breakdown` field to the `GET /api/papers/{id}`
      response, sourced from the `reproducibility_scores` row: `codeQuality` and
      `setupCompleteness` ScoreCells, `repoExists`, and `explanation`. `null` when
      no row exists, so existing reads are unaffected.
    - _Requirements: 8.1, 8.6, 8.7_

  - [x]* 7.4 Write property test — no signals means no score, not fabricated
    - Create `backend/tests/test_repro_seam_properties.py` driving the seam
      against the testcontainer DB with faked inspector + mocked LLM.
    - **Property 6: No signals at all means no score, not a fabricated one**
    - **Validates: Requirements 4.4, 6.4**

  - [x]* 7.5 Write property test — the score number never comes from the LLM
    - Vary faked `extract_setup`/`explain` outputs; assert computed scores
      unchanged.
    - **Property 7: The score number never comes from the LLM**
    - **Validates: Requirements 2.3, 4.5, 5.2, 6.7**

  - [x]* 7.6 Write property test — extraction/explanation failures degrade gracefully
    - **Property 8: Extraction and explanation failures degrade gracefully**
    - **Validates: Requirements 3.3, 5.3**

  - [x]* 7.7 Write property test — recompute updates in place, never duplicates
    - **Property 11: Recompute updates in place, never duplicates**
    - **Validates: Requirements 7.4**

  - [x]* 7.8 Write property test — the GitHub token never leaks
    - Run scoring with a sentinel `GITHUB_TOKEN`; assert it appears in no response
      body, no persisted row, no captured log output, and no LLM prompt.
    - **Property 12: The GitHub token never leaks**
    - **Validates: Requirements 1.6, 7.5**

  - [x]* 7.9 Write property/contract test — the seam preserves the paper-search contract
    - Assert the signature matches and the Score_Status resolves to `ready`/
      `unavailable`; drive a paper-search search end-to-end with the real seam and
      a faked inspector/LLM and assert the Final Score recomputes.
    - **Property 13: The seam preserves the paper-search contract**
    - **Validates: Requirements 6.1, 6.3, 6.5, 6.6**

  - [x]* 7.10 Write example/edge tests
    - Create `backend/tests/test_repro_seam.py`: no repo + extraction fails →
      `unavailable`; no repo + setup present → real score; GitHub 404 vs timeout
      mapping through the seam; explainer failure → score persists without
      explanation; score the same paper twice → one row each, updated; happy-path
      end-to-end with mirror onto `papers` + breakdown on the detail response.
    - _Requirements: 4.3, 4.4, 5.3, 6.3, 7.4_

- [x] 8. Checkpoint — backend seam
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [x] 9. Frontend — detail-view breakdown, Experiment Setup, explanation (manual verification)
  - [x] 9.1 Extend the `PaperDetail` type and client for the breakdown
    - In `frontend/src/api/papers.ts` extend `PaperDetail` with the agreed
      `experimentSetup` object shape and the nullable `reproducibilityBreakdown`
      (`codeQuality`, `setupCompleteness` ScoreCells, `repoExists`, `explanation`).
      No new route/client.
    - _Requirements: 8.1, 8.4, 8.6_

  - [x] 9.2 Populate the reproducibility breakdown in `PaperDetail`
    - In `frontend/src/components/PaperDetail.tsx` show the Reproducibility Score
      with its contributing Code-Quality Score and Setup_Completeness, each
      labeled, replacing the stubbed value; render pending/unavailable via the
      existing Score_Status rendering; when `reproducibilityBreakdown` is null,
      fall back to the plain reproducibility ScoreCell.
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 9.3 Populate the Experiment Setup section and explanation
    - Render the Experiment Setup (hyperparameters/datasets/environment), marking
      each absent field "not provided" (R8.4); when `available=false` show a
      "could not be extracted" indicator (R8.5); show the explanation alongside
      the breakdown when present (R8.6); indicate the repository-absent condition
      so the Reader sees it lowered the score (R8.7).
    - _Requirements: 8.4, 8.5, 8.6, 8.7_

- [x] 10. Final checkpoint
  - Backend: ensure all tests pass (`cd backend && uv run pytest`), including the
    token-leak assertion and the paper-search-contract test. Frontend: manually
    verify a paper detail shows the real breakdown, Experiment Setup (with absent
    fields and the unavailable case), the explanation, and the repo-absent
    indication; confirm a search's reproducibility score fills in from `pending`
    to a real value. Ask the user if questions arise.

## Redesign: standard-based scoring (ADRs 0007/0008/0009)

This section revises the already-implemented scorer to evaluate a `Paper` against
a `Reproducibility Standard` selected by its `Domain` (ML Checklist for CS, FAIR
for Medicine, baseline for unknown), replacing the ad-hoc blend. The rule-based
number, token-security, and paper-search-seam contracts are unchanged.

- [x] 11. Business logic — the standard adapter and domain selection
  - [x] 11.1 Define the standard interface and shared result shapes
    - Create `backend/app/services/repro/standards/__init__.py` with
      `CriterionStatus` enum, `CriterionResult`, `Evidence`, `StandardResult`
      dataclasses, the `ReproducibilityStandard` Protocol, the deterministic
      `roll_up(criteria)` function (met=1/partial=0.5/unmet=0, N-A excluded), and
      `select_standard(domain)`. No LLM import in `roll_up`.
    - _Requirements: 10.1, 10.2, 4.2, 4.6_
  - [x] 11.2 Implement the three standards (scoped ~6 criteria each)
    - `ml_checklist.py`, `fair.py`, `baseline.py`, each judging its criteria from
      `Evidence`; a criterion a heuristic cannot decide calls the bounded LLM
      criterion-evidence helper (evidence as data only). Criteria scoped to
      gatherable evidence (R10.5).
    - _Requirements: 10.3, 10.4, 10.5, 4.3, 4.5_
  - [x] 11.3 Rewrite `Reproducibility_Scorer` (`repro/scorer.py`) to the standard
    - `reproducibility(domain, evidence) -> StandardResult`: select the standard,
      evaluate, return the `StandardResult` whose `score` is the roll-up. Keep no
      LLM import in the roll-up path.
    - _Requirements: 4.2, 4.3, 4.4, 4.6, 10.3_
  - [ ]* 11.4 Property tests — roll-up deterministic/in-range; N-A excluded;
    standard selection by domain; number unaffected by LLM evidence (reuse
    Properties 4 and 7 against the new shape).
    - _Requirements: 4.2, 4.5, 4.6, 10.2_

- [x] 12. Backend — domain capture at ingestion
  - [x] 12.1 Add `PaperDomain` enum + `papers.domain` column
    - Add the enum and `domain` field to `app/models/paper.py`; register for
      autogenerate.
    - _Requirements: 9.4_
  - [x] 12.2 Carry domain through ingestion
    - Add `domain` to `SourceRecord` and `MergedPaper`/`_fold` (prefer a known
      domain over `unknown` on merge); read `primary_topic.field.id` in OpenAlex
      `_map` and the Atom category in arXiv `_map`; map to the enum, else
      `unknown` (R9.1–R9.3).
    - _Requirements: 9.1, 9.2, 9.3_
  - [x] 12.3 Alembic migration for `papers.domain`
    - Generate + review a migration adding the column with default/backfill
      `unknown`; commit under `backend/alembic/versions/`.
    - _Requirements: 9.4_
  - [ ]* 12.4 Example tests — OpenAlex field id / arXiv category → domain mapping,
    including the `unknown` fallback and merge preference.
    - _Requirements: 9.1, 9.2, 9.3_

- [x] 13. Backend — persist and surface the Standard Result
  - [x] 13.1 Add `standard_key` + `criteria` JSON to `ReproducibilityScore`
    - Extend the model and add an Alembic migration (nullable, additive).
    - _Requirements: 7.1_
  - [x] 13.2 Wire the seam to the standard
    - In `services/reproducibility.py`, build `Evidence` (repo signals,
      code-quality, setup, completeness, and for a Writer-claimed paper the
      manuscript/source), load `paper.domain`, call
      `reproducibility(domain, evidence)`, and persist the `StandardResult`
      (`score`, `standard_key`, `criteria`) alongside the existing breakdown.
    - _Requirements: 6.2, 6.7, 7.1_
  - [x] 13.3 Extend `reproducibility_breakdown` on `GET /api/papers/{id}`
    - Add `standardKey`, `standardName`, and the `criteria` list to the additive,
      nullable breakdown object.
    - _Requirements: 8.1, 8.8_
  - [ ]* 13.4 Example tests — a CS paper routes to ML Checklist and a Medicine
    paper to FAIR; the persisted `criteria` round-trips onto the detail response;
    `unknown` → baseline.
    - _Requirements: 9.5, 10.2, 8.8_

- [x] 14. Frontend — surface the standard and criteria (manual verification)
  - [x] 14.1 Extend `PaperDetail` / client with `standardKey`, `standardName`,
    `criteria`.
    - _Requirements: 8.1, 8.8_
  - [x] 14.2 Render the standard name and the per-Criterion list (title, status
    badge, evidence note) in `PaperDetail.tsx`, using the `frontend-design` skill
    for the criteria presentation.
    - _Requirements: 8.1, 8.8_

- [x] 15. Redesign checkpoint
  - Backend: `cd backend && uv run pytest` passes. Frontend: manually verify a CS
    paper shows "ML Reproducibility Checklist" with its criteria, a Medicine paper
    shows "FAIR", and an unknown-domain paper shows the baseline — each with
    per-criterion statuses and notes.


## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; they
  are all tests. The core scoring flow (unmarked tasks) is required.
- **This feature unstubs paper-search** by replacing the body of
  `services/reproducibility.py` at the same signature — no other paper-search
  module changes except the additive `reproducibility_breakdown` field on the
  detail response (task 7.3).
- **The number is rule-based:** `code_quality.py`, `completeness.py`, `scorer.py`
  have no LLM import; the LLM only extracts the Experiment Setup and explains the
  score (Property 7).
- **Token security is a gate:** the GitHub token is env-only, HTTPS-only, never
  logged/persisted/returned/prompted; the token-leak test (task 7.8) verifies it.
- **experiment_setup is mirrored in the same transaction** as the normalized
  `experiment_setups` upsert, so paper-search's detail read path is unchanged and
  the two never drift.
- GitHub and the LLM are **mocked/faked in all tests** — never called for real.
- Backend gate: `cd backend && uv run pytest` (pytest + testcontainers, host).
  Property tests use Hypothesis at ≥100 iterations.
- Schema via a committed Alembic migration; never `create_all`.
- Frontend has no automated test gate; verify UI manually.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "5.2"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "3.1", "3.2", "3.3", "5.1"] },
    { "id": 2, "tasks": ["1.5", "1.6", "1.7", "1.8", "1.9", "3.4", "3.5", "3.6", "5.3", "9.1"] },
    { "id": 3, "tasks": ["5.4", "5.5", "7.1", "9.2", "9.3"] },
    { "id": 4, "tasks": ["7.2", "7.3"] },
    { "id": 5, "tasks": ["7.4", "7.5", "7.6", "7.7", "7.8", "7.9", "7.10"] }
  ]
}
```

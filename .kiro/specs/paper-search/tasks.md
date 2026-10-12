# Implementation Plan: paper-search

## Overview

This plan implements the `paper-search` feature in dependency order across the
three mandated layers: Business Logic (`services/`: source adapters, merge,
ranking, LLM, reproducibility stub), Backend persistence + `Search_API` +
async scoring, and Frontend `Search_UI`. Each layer builds on the previous one
and ends by wiring the pieces together, so there is no orphaned code.

- **Backend verification gate:** after every backend task, `cd backend && uv run pytest`
  must pass (pytest + testcontainers against a throwaway `postgres:17`, run on
  the host per `backend/README.md`). External Sources and the LLM are **mocked/
  faked in tests** — never called for real — so tests stay deterministic and
  offline.
- **Schema:** the `papers` table is created by an Alembic migration committed
  under `backend/alembic/versions/` and applied via `alembic upgrade head`
  (the container entrypoint) — **never** `create_all`.
- **New dependencies:** backend deps are added via `uv` (`httpx` for Source
  adapters, `langchain` + the Bedrock integration, and `hypothesis` in the dev
  group); frontend deps (if any) via `pnpm`.
- **Frontend verification:** there is **no automated frontend test gate** — the
  team tests the UI manually. Frontend tasks are verified manually; do not invent
  a frontend test suite.
- **Ranking stays non-AI:** `services/ranking.py` is pure arithmetic with no LLM
  import; the LLM only expands the query and writes per-result relevance.
- **Reproducibility is stubbed** behind `services/reproducibility.py` so search
  and ranking ship before `reproducibility-scoring`.
- Property-based tests use **Hypothesis** (min. 100 iterations each) and are
  tagged with a comment referencing the design property they validate.

## Tasks

- [ ] 1. Business logic — ranking, merge, and the reproducibility stub (pure)
  - [ ] 1.1 Implement the non-AI `Final Score` blend (`services/ranking.py`)
    - Create `backend/app/services/ranking.py` with no LLM/HTTP/DB imports.
    - `final_score(relevance, reproducibility, *, w_rel, w_repro)`: return
      `w_rel*relevance + w_repro*reproducibility` when both components are
      present; return `None` (→ Final Score pending) if either is absent. Clamp
      inputs to `[0,1]`.
    - Add a helper to sort scored papers by Final Score descending with
      `pending` Final Scores ordered last.
    - _Requirements: 4.3, 4.4, 5.7, 8.5_

  - [ ] 1.2 Implement the common pre-merge record shape and `Merge_Dedup`
    - Create `backend/app/services/sources/base.py` with the `SourceRecord`
      dataclass (title, authors, abstract, published_date, doi, arxiv_id,
      source_links, repo_url, source) and a `SourceAdapter` Protocol
      (`name`, `fetch(query, *, limit, timeout)`), plus a `SourceError`.
    - Create `backend/app/services/merge.py`: `same_publication(a, b)` heuristic
      (normalized DOI match, OR normalized arXiv-id match, OR normalized-title
      match with overlapping authors) and `merge_dedup(record_groups)` that
      collapses same-publication records into one `MergedPaper`, recording every
      contributing source and keeping the richer non-empty value per field.
    - _Requirements: 7.1, 7.3, 7.4, 7.6_

  - [ ] 1.3 Implement the reproducibility stub seam (`services/reproducibility.py`)
    - Create `backend/app/services/reproducibility.py` with
      `score_reproducibility(paper_id) -> float` returning a fixed in-range value
      (e.g. 0.5). This is the single seam `reproducibility-scoring` will replace;
      keep it in its own module so that later spec swaps one file.
    - _Requirements: 5.6_

  - [ ] 1.4 Add Hypothesis to the dev dependency group
    - From `backend/`, run `uv add --group dev hypothesis`; confirm it lands in
      `pyproject.toml` dev group and `uv.lock`.
    - _Requirements: 5.7_

  - [ ]* 1.5 Write property test — Final Score is the exact configured non-AI blend
    - Create `backend/tests/test_ranking_properties.py`.
    - **Property 1: Final Score is the exact configured non-AI blend**
    - **Validates: Requirements 5.7, 8.5**

  - [ ]* 1.6 Write property test — Final Score pending exactly when a component is pending
    - **Property 2: Final Score is pending exactly when a component is pending**
    - **Validates: Requirements 2.3, 4.4, 5.3**

  - [ ]* 1.7 Write property test — sorted by Final Score, pending last
    - **Property 3: Results are sorted by Final Score, pending last**
    - **Validates: Requirements 4.3, 4.4**

  - [ ]* 1.8 Write property test — de-dup merges same-publication records, keeps all sources
    - Create `backend/tests/test_merge_properties.py`.
    - **Property 4: De-duplication merges same-publication records and keeps all sources**
    - **Validates: Requirements 7.3, 7.4**

  - [ ]* 1.9 Write property test — merge keeps the richer value, no full text
    - **Property 5: Merge keeps the richer value and never fabricates full text**
    - **Validates: Requirements 7.3, 7.6, 9.1**

- [ ] 2. Checkpoint — ranking, merge, stub
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [ ] 3. Source adapters and LLM assist (business logic, external — mocked in tests)
  - [ ] 3.1 Add the HTTP and LangChain/Bedrock dependencies via uv
    - From `backend/`, run `uv add httpx` and the LangChain + Bedrock packages
      (e.g. `uv add langchain langchain-aws`); confirm `pyproject.toml` and
      `uv.lock`. Pin to current stable; do not switch package managers.
    - _Requirements: 7.1, 8.1_

  - [ ] 3.2 Implement the OpenAlex Source_Adapter
    - Create `backend/app/services/sources/openalex.py` implementing
      `SourceAdapter`: query the keyless OpenAlex REST API with `httpx`, map works
      to `SourceRecord`, restrict to the CS + Medicine domains via OpenAlex
      field/concept filters, extract a repo URL when present. Index metadata/links
      only — never full text. Raise `SourceError` on failure/timeout.
    - _Requirements: 7.1, 7.2, 7.5, 7.6_

  - [ ] 3.3 Implement the arXiv Source_Adapter
    - Create `backend/app/services/sources/arxiv.py` implementing `SourceAdapter`:
      query the arXiv API with `httpx`, map entries to `SourceRecord`, restrict to
      CS categories (and Medicine-adjacent where applicable). Index metadata/links
      only. Raise `SourceError` on failure/timeout.
    - _Requirements: 7.1, 7.2, 7.5, 7.6_

  - [ ] 3.4 Implement `Query_Assist` and `Relevance_Assessment` (`services/llm.py`)
    - Create `backend/app/services/llm.py` using Amazon Bedrock via LangChain
      (model id + region from `Settings`): `expand_query(raw) -> str` (caller
      falls back to `raw` on failure/timeout) and
      `assess_relevance(paper, query) -> RelevanceResult{score 0..1, blurb}`
      (raises on failure so the orchestrator records relevance `unavailable`;
      clamp the score to `[0,1]`). No ranking logic in this module.
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6_

  - [ ]* 3.5 Write example/edge tests for adapters and LLM failure handling
    - Create `backend/tests/test_sources.py`: with mocked `httpx` responses,
      assert each adapter maps a sample record to `SourceRecord`, applies the
      domain scope, and raises `SourceError` on a simulated failure/timeout.
      Assert `expand_query` falls back and `assess_relevance` raises on a mocked
      LLM error (LLM client mocked — never called for real).
    - _Requirements: 7.2, 7.5, 8.2, 8.4_

- [ ] 4. Checkpoint — adapters and LLM
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [ ] 5. Data model, configuration, and migration (`Paper`, `Settings`)
  - [ ] 5.1 Implement the `Paper` SQLModel
    - Create `backend/app/models/paper.py` following the Base/Create/Read split
      from `item.py`: `ScoreStatus` enum (`pending`/`ready`/`unavailable`);
      `PaperBase` (title indexed, authors/sources/source_links as JSON columns,
      abstract, published_date, doi indexed, arxiv_id indexed, repo_url);
      `Paper(table=True)` on `papers` with `id` PK, the per-component
      `*_score`/`*_status` fields + `relevance_blurb`, `experiment_setup` JSON,
      `created_at` (UTC); and `PaperRead` exposing `ScoreCell`
      (`{status, value}`) for each component plus `blurb`, `experiment_setup`.
    - Register the model in `app/models/__init__.py` so it is picked up by
      `SQLModel.metadata` (tests' `create_all`) and Alembic autogenerate.
    - _Requirements: 9.1, 9.3, 9.5, 6.3, 6.4_

  - [ ] 5.2 Extend `Settings` with ranking weights, source scope, and Bedrock config
    - In `backend/app/core/config.py` add `relevance_weight: float = 0.7`,
      `reproducibility_weight: float = 0.3`, `source_domains`,
      `source_result_limit`, `source_timeout_seconds`, `llm_timeout_seconds`,
      `aws_region`, and `bedrock_model_id: str` with **no default**.
    - Document `BEDROCK_MODEL_ID`, `AWS_REGION`, and the AWS credential vars in
      `.env.example` (placeholders only); set real values in `.env` (gitignored).
    - _Requirements: 5.7, 7.2, 8.6, 9.6_

  - [ ] 5.3 Generate and review the Alembic migration for the `papers` table
    - Generate: `docker compose exec backend uv run alembic revision --autogenerate -m "create papers table"`.
    - Review the draft so it creates `papers` with indexes on `title`, `doi`, and
      `arxiv_id` and the JSON columns; commit it under
      `backend/alembic/versions/`. Applied by `alembic upgrade head`
      (entrypoint), **not** `create_all`.
    - _Requirements: 9.1, 9.2_

  - [ ]* 5.4 Write migration smoke test
    - Extend `backend/tests/test_migrations.py` with an upgrade → downgrade →
      upgrade run asserting the `papers` table and its `title`/`doi`/`arxiv_id`
      indexes exist after upgrade (single run, not PBT).
    - _Requirements: 9.2_

  - [ ]* 5.5 Write config smoke test
    - Assert constructing `Settings` without `BEDROCK_MODEL_ID` in the
      environment raises at startup (no committed default).
    - _Requirements: 9.6_

- [ ] 6. Checkpoint — model, config, migration
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [ ] 7. Scoring orchestration and `Search_API` router (backend)
  - [ ] 7.1 Implement the async scoring orchestrator (`services/scoring.py`)
    - Create `backend/app/services/scoring.py`:
      `schedule_scoring(paper_ids, query, tasks)` queues one `BackgroundTasks`
      job per paper; `run_scoring_for_paper(paper_id, query)` opens its own
      `Session`, computes `assess_relevance` and `score_reproducibility`,
      attaches each value with status `ready` (or `unavailable` on failure),
      recomputes the Final Score via `ranking.final_score` using the configured
      weights, and persists. Guarantee no component is left `pending` after the
      job runs.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6, 5.7, 8.4_

  - [ ] 7.2 Implement the search fetch/merge/cache pipeline helper
    - In `services/scoring.py` (or a small `services/pipeline.py`): given a raw
      query, call `expand_query` (fall back to raw on failure), fan out to the
      configured adapters with the configured timeout/limit, collect records and
      the set of failed sources, run `merge_dedup`, then **upsert** each merged
      paper into `papers` — look up an existing row by `doi` else `arxiv_id` and
      reuse it (merging newly-contributing sources) rather than inserting a
      duplicate. Return the cached paper ids and `failed_sources`.
    - _Requirements: 4.1, 4.2, 7.5, 9.1, 9.4, 9.5_

  - [ ] 7.3 Implement `routers/papers.py` endpoints
    - Create `backend/app/routers/papers.py` with `APIRouter(prefix="/api/papers")`
      using the existing `get_session` dependency.
    - `POST /search`: validate query (non-empty, ≤512, non-whitespace) → `422`
      with no fetch; run the fetch/merge/cache pipeline; if **all** sources failed
      → `502 {source_failure: true}` (distinct from `200 {papers: []}`); schedule
      scoring via `BackgroundTasks`; return `200` with the papers sorted by Final
      Score (pending last), all component ScoreCells, and `failed_sources`.
    - `GET /scores?ids=`: return current component ScoreCells + Final Score +
      blurb for each requested cached paper; omit unknown ids.
    - `GET /{paper_id}`: serve `PaperRead` from the cache (no Source re-fetch);
      `404` for an uncached id. Return `repo_url`/`experiment_setup` as absent
      when not present.
    - _Requirements: 1.* (API side), 4.1, 4.3, 4.4, 4.5, 4.6, 4.7, 5.2, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ] 7.4 Register the papers router in `main.py`
    - Add `app.include_router(papers.router)` in `backend/app/main.py`; leave
      `/health` and `/api/items` routes untouched. This wires the backend
      together.
    - _Requirements: 4.1, 5.5, 6.1_

  - [ ]* 7.5 Write property test — one source failing never fails the search
    - Create `backend/tests/test_search_api_properties.py` driving endpoints via
      `TestClient` against the testcontainer DB, with **faked adapters** and a
      **mocked LLM**.
    - **Property 6: One source failing never fails the search**
    - **Validates: Requirements 4.6, 4.7, 7.5**

  - [ ]* 7.6 Write property test — query validation rejects before any fetch
    - Assert faked adapters/LLM are **not** called for invalid queries.
    - **Property 7: Query validation rejects before any fetch**
    - **Validates: Requirements 1.1, 4.5**

  - [ ]* 7.7 Write property test — caching persists Papers but never the query
    - **Property 8: Caching persists Papers but never the query**
    - **Validates: Requirements 4.2, 9.1**

  - [ ]* 7.8 Write property test — re-search reuses cached Papers rather than duplicating
    - **Property 9: Re-search reuses cached Papers rather than duplicating**
    - **Validates: Requirements 9.4, 9.5**

  - [ ]* 7.9 Write property test — score lifecycle terminates (no permanent pending)
    - Run the scheduled scoring jobs (faked LLM success and failure) and assert
      each component ends `ready` or `unavailable`.
    - **Property 10: Score lifecycle terminates — no component stays pending forever**
    - **Validates: Requirements 5.3, 5.4, 8.4**

  - [ ]* 7.10 Write property test — reproducibility stub produces a full score lifecycle
    - **Property 11: The reproducibility stub produces a full score lifecycle**
    - **Validates: Requirements 5.6**

  - [ ]* 7.11 Write property test — detail served from cache, 404 for unknown ids
    - Assert the detail path does **not** call any adapter.
    - **Property 12: Detail is served from cache and 404s for unknown ids**
    - **Validates: Requirements 6.1, 6.2, 6.5**

  - [ ]* 7.12 Write example/edge tests for endpoints
    - Create `backend/tests/test_search_api.py`: R4.5 empty/whitespace/513-char
      query → `422`; all-adapters-fail → `502 source_failure` vs. succeed-with-
      zero-records → `200 {papers: []}`; one-fails-one-succeeds → results +
      failed source listed; end-to-end search → scores-poll → detail happy path.
    - _Requirements: 4.5, 4.6, 4.7, 5.5, 6.1_

- [ ] 8. Checkpoint — backend Search_API
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [ ] 9. Frontend — `Search_UI` (manual verification; no automated test gate)
  - [ ] 9.1 Add any required frontend dependencies via pnpm
    - If the UI needs packages beyond the existing stack (e.g. a router), add them
      from `frontend/` with `pnpm add <pkg>` (pinned). If none are needed, note
      that explicitly and skip. Do not switch package managers.
    - _Requirements: 1.1, 2.6, 3.1_

  - [ ] 9.2 Implement the typed API client `api/papers.ts`
    - Create `frontend/src/api/papers.ts` with the `ScoreStatus`/`ScoreCell`/
      `PaperCard`/`PaperDetail` types and `search` (30s timeout, abandons the
      previous in-flight call), `scores(ids)`, and `paper(id)` (30s timeout).
      Every call uses `credentials: "include"` and a per-request
      `AbortController`.
    - _Requirements: 1.2, 1.3, 1.6, 1.7, 2.7, 3.1, 3.7, 5.5_

  - [ ] 9.3 Implement `SearchBox`
    - Create `frontend/src/components/SearchBox.tsx`: search input + submit;
      submit disabled while empty/whitespace; loading indicator + disabled submit
      during the request; empty-result message; error/retry on timeout/network,
      retaining the query; a new submit abandons the previous request.
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [ ] 9.4 Implement `ResultList` + `ResultCard`
    - Create `frontend/src/components/ResultList.tsx` and `ResultCard.tsx`: render
      cards in the API's returned order; each card shows title, authors, a Source
      badge per contributing Source, the three labeled component scores,
      pending/unavailable rendering, the relevance blurb when present, and
      navigates to the detail view on activation.
    - _Requirements: 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ] 9.5 Implement `useScorePolling` for live score updates
    - Create `frontend/src/components/useScorePolling.ts`: while any rendered card
      has a `pending` component, poll `scores(ids)` on an interval, replace each
      pending cell with its value or `unavailable`, re-sort when a Final Score
      resolves, and stop when nothing is pending or after a bounded number of
      attempts — no resubmission by the Reader.
    - _Requirements: 2.7, 5.5_

  - [ ] 9.6 Implement `PaperDetail`
    - Create `frontend/src/components/PaperDetail.tsx`: fetch by id; render title,
      authors, abstract, publication date, every Source badge, external source
      links, the full score breakdown with each Score_Status, the repo link or
      "no repository" indicator, the Experiment Setup section (or "not yet
      available"), and the opt-in/off-by-default code-generation action whose
      availability depends on repo presence (behavior deferred to
      `code-generation`); not-found message with a path back to search; error/
      retry on timeout/failure.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [ ] 9.7 Wire Search_UI into `App.tsx`
    - Render the search view (`SearchBox` + `ResultList`) and the `PaperDetail`
      view, switching between them on card activation / back. This integrates the
      frontend end-to-end.
    - _Requirements: 1.4, 2.6, 3.1, 3.6_

- [ ] 10. Final checkpoint
  - Backend: ensure all tests pass (`cd backend && uv run pytest`). Frontend:
    manually verify search → ranked cards with pending scores filling in → Paper
    detail → back, including the empty-result and source-failure states. Ask the
    user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; they
  are all tests. The core search flow (unmarked tasks) is required.
- **Reproducibility is stubbed** (`services/reproducibility.py`, task 1.3); when
  `reproducibility-scoring` ships it replaces that one module behind the same
  signature, and the real Experiment Setup fills the `experiment_setup` column —
  no other `paper-search` code changes.
- **Ranking never calls the LLM:** `services/ranking.py` is pure arithmetic; the
  LLM only expands the query (`Query_Assist`) and writes per-result relevance
  (`Relevance_Assessment`).
- External Sources and the LLM are **mocked/faked in all tests** — never called
  for real — so the backend gate is deterministic and offline.
- Each task references specific requirements and/or design Property numbers for
  traceability.
- Backend gate: `cd backend && uv run pytest` (pytest + testcontainers, run on
  the host). Property tests use Hypothesis at ≥100 iterations.
- Schema is created by a committed Alembic migration under
  `backend/alembic/versions/` and applied via `alembic upgrade head` — never
  `create_all` (that exists only for test speed).
- Frontend has no automated test gate; verify UI manually.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4", "3.1", "5.1", "5.2", "9.1"] },
    { "id": 1, "tasks": ["1.5", "1.6", "1.7", "1.8", "1.9", "3.2", "3.3", "3.4", "5.3", "9.2"] },
    { "id": 2, "tasks": ["3.5", "5.4", "5.5", "7.1", "7.2", "9.3", "9.6"] },
    { "id": 3, "tasks": ["7.3", "9.4", "9.5"] },
    { "id": 4, "tasks": ["7.4", "9.7"] },
    { "id": 5, "tasks": ["7.5", "7.6", "7.7", "7.8", "7.9", "7.10", "7.11", "7.12"] }
  ]
}
```

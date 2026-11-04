# Implementation Plan: demo-mode

## Overview

This plan implements `demo-mode` bottom-up: settings, then the Cassette and the
generic `cached()` state machine, then the three seam wrappers wired into the
existing call sites, then the inline-scoring/ordering change in the Search_API,
then the demo scripts and docs. Each layer ends with a checkpoint, and the last
task is a manual rehearsal, because the point of the feature is a repeatable live
demo. There is no frontend change, no table and no migration.

- **Backend verification gate:** after every backend task, `cd backend && uv run pytest`
  must pass (pytest + testcontainers against a throwaway `postgres:17`, run on the
  host per `backend/README.md`). With `DEMO_MODE` unset the whole existing suite is
  the regression gate for `off`.
- **Schema:** none. No Alembic migration is needed; do not use `create_all`.
- **AI and network calls:** every test fakes the sources, Bedrock and GitHub. **No
  test calls a live source, Bedrock or GitHub.** A fake that must not be called
  raises.
- **Dependencies:** none new. Hypothesis is already in the dev group. `uv` and
  `pnpm` only.
- **Existing patch points must keep working.** Tests monkeypatch `llm._client`,
  `extractor._client`, `scoring._ADAPTERS`, `scoring.expand_query`, and
  `inspector.inspect_repo`; keep every one of those names and signatures.
- **Frontend verification:** there is **no automated frontend test gate** and no
  frontend change in this spec. The *Final score* parity is covered by Property 11
  and checked manually in the final task.
- Property-based tests use **Hypothesis** (min. 100 iterations each) and are tagged
  with a comment referencing the design property they validate, in the form
  `# Feature: demo-mode, Property N: <title>`.

## Tasks

- [x] 1. Backend — settings, startup log, compose wiring
  - [x] 1.1 Add the `Settings` fields
    - In `backend/app/core/config.py` add `demo_mode: Literal["off", "record",
      "replay"] = "off"` and `demo_cassette_path: str = "demo/fixtures/cassette.json"`
      (import `Literal` from `typing`). Pydantic's validation provides the
      startup failure for any other value, naming the field and the accepted
      values.
    - _Requirements: 1.1, 1.2, 1.4, 8.1_

  - [x] 1.2 Log the mode at startup
    - In `backend/app/main.py` `lifespan`, when `settings.demo_mode != "off"`, log
      one line `demo mode=<mode> cassette=<path>` on the `uvicorn.error` logger at
      INFO. Log nothing for `off`.
    - _Requirements: 8.3_

  - [x] 1.3 Wire compose and document the settings
    - In `compose.yaml` (backend service) add `DEMO_MODE: ${DEMO_MODE:-off}` and
      `DEMO_CASSETTE_PATH: ${DEMO_CASSETTE_PATH:-/demo/fixtures/cassette.json}` with
      a short comment, and a `volumes:` entry `- ./demo:/demo`.
    - Add both variables to `.env.example` with `DEMO_MODE=off` and a comment on the
      three values (placeholders only).
    - Create `demo/fixtures/.gitkeep` so the mount source and the fixtures folder
      exist in a fresh clone.
    - _Requirements: 1.5, 1.6_

  - [x]* 1.4 Write example tests — settings and startup log
    - In `backend/tests/test_demo_settings.py`: defaults are `off` and the documented
      path (1.1, 1.4); `DEMO_MODE=bogus` raises a validation error that names
      `demo_mode` and the accepted values (1.2); the startup log line appears for
      `record`/`replay` and not for `off` (8.3). Build `Settings()` directly with
      `monkeypatch.setenv`; do not rely on the cached `get_settings()`.
    - _Requirements: 1.1, 1.2, 1.4, 8.1, 8.3_

- [x] 2. Business logic — `Cassette_Store` and `cached()` (`services/demo/cassette.py`)
  - [x] 2.1 Implement the store and request keys
    - Create `backend/app/services/demo/__init__.py` and
      `backend/app/services/demo/cassette.py` with no FastAPI/SQLModel/domain
      imports.
    - `CassetteError(Exception)`; `request_key(seam: str, key_input: dict) -> str`
      returning `f"{seam}:{sha256_hex}"` of `json.dumps(key_input, sort_keys=True,
      separators=(",", ":"), ensure_ascii=False)` encoded as UTF-8.
    - `Cassette_Store` with `get(key) -> dict | None` and `put(key, entry)`: loads
      the file lazily once per process under a `threading.RLock`; missing file is
      empty; invalid JSON or `version != 1` raises `CassetteError` naming the path
      and the file is never written; writes `json.dumps(doc, sort_keys=True,
      indent=2, ensure_ascii=False) + "\n"` to a temp file in the same directory
      (creating the parent directory if needed), `fsync`s, then `os.replace`s it.
    - Secret guard in `put`: serialize the entry; for each non-empty secret in
      (`os.environ["AWS_SECRET_ACCESS_KEY"]`, `settings.github_token`,
      `settings.session_secret`) raise `CassetteError` if it is a substring, before
      any write.
    - Provide a module-level accessor that builds the store from
      `get_settings().demo_cassette_path` (and can be reset in tests).
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 8.2, 8.4_

  - [x] 2.2 Implement `cached()`
    - In the same module add `cached(seam, key_input, live, encode, decode, label="")`
      exactly as the design's state machine: `off` calls `live()` and never touches
      the store; `replay` returns `decode(entry["recorded"])` on a hit, and on a miss
      logs one warning with the seam and the key digest only (no prompt text) and
      returns `live()` without writing; `record` calls `live()` (letting exceptions
      propagate, storing nothing), then stores `{seam, label, model, recorded}` under
      the key (replacing any existing entry) and returns the live result. Read
      `get_settings` through a module-level name so tests can patch it.
    - `model` is `settings.bedrock_model_id` for the `llm` seam and omitted for
      others.
    - _Requirements: 1.3, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.3, 4.4, 4.5_

  - [x]* 2.3 Write property tests — request keys and serialization
    - `backend/tests/test_demo_cassette_properties.py`, using a `tmp_path` Cassette.
    - **Property 1** — keys are canonical (insertion-order independent, distinct
      inputs differ).
    - **Property 2** — write/load round-trips and is byte-stable regardless of
      insertion order.
    - _Requirements: 2.1, 2.2, 2.3_

  - [x]* 2.4 Write property tests — record, replay, miss, off
    - **Property 3** — record then replay returns an equal result with zero live
      calls.
    - **Property 4** — a replay miss calls `live` once, logs exactly one warning
      with the seam and digest and no prompt text, and leaves the file bytes
      unchanged.
    - **Property 5** — a raising `live` in record propagates and stores nothing.
    - **Property 6** — re-recording a key leaves exactly one entry with the new
      result.
    - **Property 7** — `off` returns the live result and never reads or creates the
      Cassette path.
    - _Requirements: 1.3, 3.1, 3.2, 3.3, 3.4, 4.1, 4.3, 4.4, 4.5_

  - [x]* 2.5 Write property tests — secrets and corrupt files
    - **Property 9** — an entry containing a configured secret raises and leaves the
      file unchanged; one without it is written.
    - **Property 10** — a non-Cassette file raises `CassetteError` naming the path
      and is not modified by a later `put`.
    - _Requirements: 2.5, 2.6, 2.7, 8.2, 8.4_

- [x] 3. Checkpoint — Cassette and settings
  - Run `cd backend && uv run pytest`. Ensure it passes; ask the user if anything is
    unclear. (The seams are not wired yet, so no behavior has changed.)

- [x] 4. Business logic — seam wrappers (`services/demo/seams.py`) and wiring
  - [x] 4.1 Implement the codecs and wrappers
    - Create `backend/app/services/demo/seams.py`.
    - `_encode_records` / `_decode_records` for `list[SourceRecord]`: `published_date`
      to ISO string or null and back, `domain` to its enum value and back,
      `source_links` as a list of pairs and back to tuples.
    - RepoSignals codec: `dataclasses.asdict` and `RepoSignals(**d)`.
    - `_CassetteChat` with a lazy `_real` built from a `build` callable, and
      `invoke(prompt)` calling `cached("llm", {"prompt": prompt}, ...)` with
      `encode=lambda r: {"content": _content_text(r)}` and
      `decode=lambda d: AIMessage(content=d["content"])` (`from langchain_core.messages
      import AIMessage`; import `_content_text` from `app.services.llm` **inside**
      the function to avoid an import cycle); `label=prompt[:80]`.
    - `wrap_chat(build)` returns `build()` when `demo_mode == "off"` else
      `_CassetteChat(build)`.
    - `_CassetteSource` and `wrap_source(adapter)` (returns the adapter unchanged
      when `off`), keying on `{"source": name, "query": query, "limit": limit,
      "domains": settings.source_domains}`.
    - Expose a `cached_repo(repo_url, live)` helper keying on `{"repo_url":
      repo_url.strip()}`.
    - _Requirements: 4.2, 4.6, 5.1, 5.2, 5.3, 5.5_

  - [x] 4.2 Wire the LLM seam
    - In `services/llm.py`, `services/repro/extractor.py` and
      `services/repro/explainer.py`, change the **body** of each `_client()` to
      `return wrap_chat(lambda: ChatBedrock(model=..., region_name=...))`. Keep the
      function names, signatures, the `lru_cache` on `llm._client`, and every caller
      unchanged. Do **not** touch `core/codegen.py`.
    - _Requirements: 4.2, 5.2, 5.4, 5.5_

  - [x] 4.3 Wire the source seam
    - In `services/scoring.py`, make `_adapters()` return
      `[wrap_source(a) for a in _ADAPTERS]`. `run_search` is unchanged.
    - _Requirements: 5.1, 5.5_

  - [x] 4.4 Wire the repo seam
    - In `services/repro/inspector.py` `inspect_repo`, keep the early return for an
      absent or blank URL first (no lookup), and wrap the host call:
      `cached_repo(repo_url, lambda: _HOST.inspect(repo_url, timeout=...))`.
    - _Requirements: 5.3, 5.5, 5.6_

  - [x]* 4.5 Write property test — codecs round-trip
    - **Property 8** — for any `SourceRecord` (date `None` or set, every
      `PaperDomain`, any `source_links`), any `RepoSignals`, and any LLM string
      (empty, non-ASCII), `decode(encode(x)) == x`.
    - _Requirements: 4.6, 5.1, 5.2, 5.3_

  - [x]* 4.6 Write example tests — seam wiring
    - `backend/tests/test_demo_seams.py`: a paper with no repo URL performs no repo
      lookup in `replay` (5.6); codegen's `_client` is unchanged and still follows
      `CODEGEN_MOCK` in every mode (5.4); with `DEMO_MODE=off`, `wrap_chat` returns
      the real client and `wrap_source` returns the adapter (5.5); in `replay` with
      empty AWS credentials and a hit, no `ChatBedrock` is constructed (4.2).
    - _Requirements: 4.2, 5.4, 5.5, 5.6_

- [ ] 5. Checkpoint — seams
  - Run `cd backend && uv run pytest`. Ensure it passes, including the existing
    monkeypatch-based tests; ask the user if anything is unclear.

- [ ] 6. Backend — inline scoring and deterministic ordering
  - [ ] 6.1 Add `ranking.sort_deterministic`
    - In `backend/app/services/ranking.py` add the pure function from the design:
      key `(not ready, -(final_score or 0.0), id)` where `ready` is
      `final_status is ScoreStatus.ready and final_score is not None`. Keep the file
      free of LLM, HTTP and DB imports (import only the enum). Leave
      `sort_by_final_score` untouched.
    - _Requirements: 6.3_

  - [ ] 6.2 Score inline and branch the router
    - In `services/scoring.py` add `score_inline(paper_ids, query)` looping
      `run_scoring_for_paper(pid, query)` in order.
    - In `routers/papers.py` `search`, after the unchanged `all_failed` check: when
      `get_settings().demo_mode == "off"` keep `schedule_scoring` and
      `ranking.sort_by_final_score`; otherwise call `scoring.score_inline`, then
      `session.expire_all()`, reload the papers, and order with
      `ranking.sort_deterministic`. Response shape and status codes are unchanged.
    - _Requirements: 6.1, 6.2, 6.4, 6.7_

  - [ ]* 6.3 Write property test — ordering is total and a fixed point of the frontend sort
    - **Property 11** — for any papers with arbitrary statuses and scores,
      `sort_deterministic` orders ready papers by Final Score descending then id
      ascending with non-ready/`None` last, and a Python mirror of the frontend
      *Final score* comparator (value if ready else −1, descending, stable) leaves
      that ordering unchanged. Cite `useScorePolling.ts` `rankBy`/`sortCards` in a
      comment.
    - _Requirements: 6.3, 6.6_

  - [ ]* 6.4 Write integration tests — inline scoring
    - `backend/tests/test_demo_search.py` through `TestClient` with fake adapters and
      fake chat/repo seams, `DEMO_MODE=replay` via a patched `get_settings`.
    - **Property 12** — every score cell in the response is `ready` or
      `unavailable`, and values come from this request's run, including for papers
      pre-seeded with stale scores and for papers whose components fail.
    - Example: `off` still returns `pending` cells and the Cassette path is never
      opened (6.7, 1.3).
    - _Requirements: 6.1, 6.2, 6.4, 6.7, 8.5_

  - [ ]* 6.5 Write integration test — replay is repeatable end to end
    - **Property 13** — record a search with fakes, then search twice in `replay`
      with every live fake made to fail the test; the three responses are identical
      in cards, order and values. Include a `Replay_Miss` example that goes live and
      leaves the Cassette bytes unchanged.
    - _Requirements: 4.1, 4.2, 6.5, 8.5_

- [ ] 7. Checkpoint — backend Search_API
  - Run `cd backend && uv run pytest`. Ensure the full suite passes with `DEMO_MODE`
    unset (the `off` regression gate) and with the new tests; ask the user if
    anything is unclear.

- [ ] 8. Demo tooling
  - [ ] 8.1 Write `scripts/demo-env.sh` and `scripts/demo-reset.sh`
    - `demo-env.sh` (sourced): exports `QUERY_EXPANSION_ENABLED=false` and
      `CODEGEN_MOCK=true`, and defines the demo account constants and a
      `wait_healthy` helper (poll `GET /health`, bounded at 120 s, non-zero on
      timeout).
    - `demo-reset.sh`: `set -euo pipefail`; `docker compose down -v`; export
      `DEMO_MODE=replay`; `docker compose up -d --build`; `wait_healthy`; `POST
      /api/auth/register` for the demo account, treating a conflict (409) as success.
      Mark executable.
    - _Requirements: 7.1, 7.2_

  - [ ] 8.2 Write `scripts/demo-record.sh`
    - Same reset with `DEMO_MODE=record`; log in with a cookie jar; for each
      non-blank, non-`#` line of `demo/queries.txt`, `POST /api/papers/search` with
      `curl -m 900`; print the ordered `title  final-score` table via a small
      `python3 -c` JSON parse; exit non-zero on any non-200 or empty result; after
      the loop `chown` the Cassette to the invoking user (`docker compose exec -T
      backend chown "$(id -u):$(id -g)" /demo/fixtures/cassette.json`). Do not
      `git add` or commit anything. Mark executable.
    - _Requirements: 7.3, 7.4, 7.6_

  - [ ] 8.3 Write `demo/queries.txt` and `demo/SCRIPT.md`
    - `queries.txt`: comment header explaining the format and **placeholder**
      lines; ask the user for the real queries (do not invent them).
    - `SCRIPT.md`: queries in presentation order with the expected top results (to
      be filled after the first record), required settings (`DEMO_MODE=replay`,
      `QUERY_EXPANSION_ENABLED=false`, `CODEGEN_MOCK=true`), which sort the presenter
      uses (the frontend defaults to *Relevance*; note when to click *Final score*),
      the re-record steps, and a one-line talking point that results are pre-recorded.
    - _Requirements: 7.5_

- [ ] 9. Docs and final verification
  - [ ] 9.1 Capture the decision and document the feature
    - Write `docs/adr/0010-demo-mode-records-and-replays-at-the-seams.md` using the
      `domain-modeling` skill's ADR format. Add a short "Demo mode" section to
      `README.md` (settings, scripts) and a one-line pointer in `CLAUDE.md`. Add a
      `GLOSSARY.md` entry for **Cassette**. Update `TODO.md`.
    - _Requirements: 7.5_

  - [ ] 9.2 Final checkpoint — manual rehearsal
    - With the user: put the real queries in `demo/queries.txt`; run
      `scripts/demo-record.sh` once against the real sources and review the printed
      order; commit the Cassette; run `scripts/demo-reset.sh` with the network and
      AWS credentials disabled; in the browser confirm each scripted query shows the
      same cards on repeat runs, that switching to *Final score* does not reorder
      them, and that code generation uses the mock. Tick this task only when the
      user confirms.
    - _Requirements: 4.2, 6.5, 6.6, 7.1, 7.3, 7.5_

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "6.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "2.2", "6.2", "6.3"] },
    { "id": 2, "tasks": ["1.4", "2.3", "2.4", "2.5", "4.1"] },
    { "id": 3, "tasks": ["3", "4.2", "4.3", "4.4", "4.5"] },
    { "id": 4, "tasks": ["5", "4.6", "6.4", "6.5", "8.1", "8.2"] },
    { "id": 5, "tasks": ["7", "8.3"] },
    { "id": 6, "tasks": ["9.1"] },
    { "id": 7, "tasks": ["9.2"] }
  ]
}
```

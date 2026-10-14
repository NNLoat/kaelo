# Summary — 1st Prototype

A snapshot of the Kaelo prototype at the end of the first build-and-test pass,
for handoff to the frontend/backend owners. It records what works, what's left,
and the operational gotchas.

## What this prototype does

An AI-assisted search engine for scientific papers that scores reproducibility
and can generate candidate code. Two roles share one account (Reader / Writer).
Stack: FastAPI + SQLModel + Alembic (backend), Vite + React + TS + Tailwind
(frontend), Postgres 17, Docker Compose. See `.kiro/steering/` for the full
product/tech/structure context.

## Status by spec

All five specs' **core (required) tasks are implemented**. What remains is manual
verification checkpoints, optional (`*`) test tasks, and documented deferrals.

| Spec | Core impl | What's left | Type | Blocking? |
|---|---|---|---|---|
| **accounts** | ✅ Done (merged) | Task 8 — final checkpoint (manual browser verify) | Manual gate | No — verified |
| **paper-search** | ✅ Done (merged) | Task 10 — final checkpoint (manual verify) | Manual gate | No — verified working |
| **reproducibility-scoring** | ✅ Done (merged) | Task 10 — final checkpoint (manual verify) | Manual gate | No — renders after PR #18 |
| **code-generation** | ✅ Done — R1–R8 merged; R9–R11 in PR #19 | Task 8 + Task 12 — manual checkpoints | Manual gate | No — pending PR #19 merge |
| **writer-workspace** | ✅ Backend + frontend done (merged) | 7 optional (`*`) tests: 1.5, 3.3, 5.6–5.11 | Optional tests | No — but coverage risk |

## Verified working in the browser (this pass)

- **accounts** — register / login / logout / Reader↔Writer mode toggle.
- **paper-search** — query → ranked result cards → paper detail page.
- **reproducibility-scoring** — scores on cards + the detail-page breakdown
  (fixed a snake_case contract mismatch that was blanking the whole app, PR #18).
- **code-generation** — Reader `generate` / `align` on the detail page; artifact
  view + download. Real generation was failing (brittle JSON parse of LLM output)
  → fixed with a delimiter format; added mock mode + a cancel control (PR #19).
- **writer-workspace** — claim a paper, upload manuscript (PDF→text) and source
  (archive or public Git URL), list/delete. Verified via API + UI.

## What's left — the detail

### 1. code-generation `writer` case is still stubbed (top priority follow-up)

The Writer upload now persists (writer-workspace shipped), but
`backend/app/routers/codegen.py` `_precondition` — the `case is Case.writer` arm
— still **hard-refuses** ("No uploaded manuscript for this paper yet…"). It was
never wired to read the persisted `WriterManuscript` / `WriterSourceFile`.

**To finish:** resolve the Writer's claim + uploads in `_precondition` and build
`GenerationInputs(manuscript_text=…, uploaded_source=…)` instead of refusing;
add a frontend trigger in the writer workspace. Touches backend + frontend. Not
yet a task in any spec — add it to the code-generation spec (R5.3 describes the
intended behavior). Depends on PR #19 being merged first.

### 2. writer-workspace backend has no dedicated tests

The 124 passing tests do **not** exercise `/api/writer/*`. The new tables,
migration, router, and Git-fetch are only covered transitively. Optional (`*`)
tasks 1.5, 3.3, 5.6–5.11 cover them. Given schema/ownership/Git-fetch stakes,
do at least **3.3** (migration smoke) and **5.11** (API edge + mocked Git-fetch).

### 3. Manual final checkpoints

No automated frontend gate — accounts/paper-search/repro/codegen each have a
"verify in browser then tick the box" final task. Most are effectively done;
codegen Task 12 needs mock-mode + cancel verified in the browser after PR #19.

### 4. Documented deferrals (intentional — not bugs)

- **accounts:** no server-side session store → no immediate logout revocation.
- **reproducibility-scoring:** Reader-side extraction is index-only
  (title + abstract); richer extraction from Writer uploads deferred to
  writer-workspace.
- **writer-workspace:** cross-identifier claim de-dup (arXiv URL vs DOI = two
  claims) deferred until paper-search/OpenAlex resolution exists.

## Open PR

- **PR #19** (`fix/codegen-parse-cancel-mock`) — MERGEABLE/CLEAN, not yet merged.
  R9–R11: generation parse fix, mock mode, job cancel.

## Operational gotchas (read before deploying/sharing)

- **Migrations aren't compose-watch-synced.** `alembic/` is baked into the
  backend image at build time; after any migration run
  `docker compose up -d --build backend` (or `alembic upgrade head`).
- **Mock mode:** `CODEGEN_MOCK=true` (wired through compose + `.env.example`)
  makes generation return a canned artifact with no Bedrock call — use it for
  deterministic frontend testing.
- **Rotate the AWS key.** `.env` still contains a leaked key
  (`AKIA6HF7RX3XVOANFSIE`) — rotate before sharing the repo.
- **Backend gate:** `cd backend && uv run pytest` → 124 passed (testcontainers
  Postgres 17, run on host). No automated frontend test gate — UI is manual.

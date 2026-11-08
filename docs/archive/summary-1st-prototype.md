# Summary — 1st Prototype

A snapshot of the Kaelo prototype at the end of the first build-and-test pass,
for handoff to the frontend/backend owners. It records what works, what's left,
and the operational gotchas.

## What this prototype does

An AI-assisted search engine for scientific papers that scores reproducibility
and can generate candidate code. Two roles share one account (Reader / Writer).
Stack: FastAPI + SQLModel + Alembic (backend), Vite + React + TS + Tailwind
(frontend), Postgres 17, Docker Compose. See `CLAUDE.md` for the full
product/tech/structure context.

## Status by spec

All five specs' **core (required) tasks are implemented**. What remains is manual
verification checkpoints, optional (`*`) test tasks, and documented deferrals.

| Spec | Core impl | What's left | Type | Blocking? |
|---|---|---|---|---|
| **accounts** | ✅ Done (merged) | Task 8 — final checkpoint (manual browser verify) | Manual gate | No — verified |
| **paper-search** | ✅ Done (merged) | Task 10 — final checkpoint (manual verify) | Manual gate | No — verified working |
| **reproducibility-scoring** | ✅ Done (merged) | Task 10 — final checkpoint (manual verify) | Manual gate | No — renders after PR #18 |
| **code-generation** | ✅ Done — R1–R11 merged; writer case wired (Task 13) | Task 8 + Task 12 — manual checkpoints | Manual gate | No — verified |
| **writer-workspace** | ✅ Backend + frontend done (merged) | 7 optional (`*`) tests: 1.5, 3.3, 5.6–5.11 | Optional tests | No — but coverage risk |

## Verified working in the browser (this pass)

- **accounts** — register / login / logout / Reader↔Writer mode toggle.
- **paper-search** — query → ranked result cards → paper detail page.
- **reproducibility-scoring** — scores on cards + the detail-page breakdown
  (fixed a snake_case contract mismatch that was blanking the whole app, PR #18).
- **code-generation** — Reader `generate` / `align` on the detail page; artifact
  view + download. Real generation was failing (brittle JSON parse of LLM output)
  → fixed with a delimiter format; added mock mode + a cancel control (PR #19).
  The **Writer** case is now wired too (Task 13): claim with an uploaded
  manuscript → Generate → artifact.
- **writer-workspace** — claim a paper (bare arXiv id, `arXiv:`-prefixed id, DOI,
  or URL), upload manuscript (PDF→text) and source (archive or public Git URL),
  list/delete. Verified via API + UI.

## What's left — the detail

### 1. writer-workspace backend has no dedicated tests

The passing suite does **not** exercise `/api/writer/*`. The tables, migration,
router, and Git-fetch are only covered transitively. Optional (`*`) tasks 1.5,
3.3, 5.6–5.11 cover them. Given schema/ownership/Git-fetch stakes, do at least
**3.3** (migration smoke) and **5.11** (API edge + mocked Git-fetch).

### 2. Manual final checkpoints

No automated frontend gate — accounts/paper-search/repro/codegen each have a
"verify in browser then tick the box" final task. Most are effectively done;
codegen Task 12 needs mock-mode + cancel verified in the browser after PR #19.

### 3. Documented deferrals (intentional — not bugs)

- **accounts:** no server-side session store → no immediate logout revocation.
- **reproducibility-scoring:** Reader-side extraction is index-only
  (title + abstract); richer extraction from Writer uploads deferred to
  writer-workspace.
- **writer-workspace:** cross-identifier claim de-dup (arXiv URL vs DOI = two
  claims) deferred until paper-search/OpenAlex resolution exists.

## Open PR

- (none) — PR #19 merged; the writer-case wiring is on branch
  `spec/codegen-writer-case` (this PR).

## Operational gotchas (read before deploying/sharing)

- **Migrations aren't compose-watch-synced.** `alembic/` is baked into the
  backend image at build time; after any migration run
  `docker compose up -d --build backend` (or `alembic upgrade head`).
- **Mock mode:** `CODEGEN_MOCK=true` (wired through compose + `.env.example`)
  makes generation return a canned artifact with no Bedrock call — use it for
  deterministic frontend testing.
- **Rotate the AWS key.** Done: the leaked key was rotated and AWS rejects the old one.
- **Backend gate:** `cd backend && uv run pytest` → 132 passed (testcontainers
  Postgres 17, run on host). No automated frontend test gate — UI is manual.

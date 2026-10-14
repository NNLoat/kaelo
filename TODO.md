# TODO

## Project context + spec workflow — DONE (Phase 0 + first feature grilled)

**Status:** The foundation steering files are complete and the product has been
grilled into shared understanding. All five feature specs are drafted
(`accounts`, `paper-search`, `reproducibility-scoring`, `code-generation`,
`writer-workspace`). Implementation is well underway — see "Implementation
status" below.

Done:

1. **Foundation steering files** in `.kiro/steering/` (always-included):
   - [x] `product.md` — filled in; corrected for the Writer-content storage
     exception (see `docs/adr/0003`).
   - [x] `tech.md` — filled in; the four "to decide" items (data sources, LLM
     provider, auth, secrets) are now settled and recorded as ADRs.
   - [x] `structure.md` — conventions confirmed (`routers/` for API routes,
     `models/` for tables, `components/` for frontend).
2. [x] **A `workflow.md` steering file** encoding the dev loop (litmus test,
   "feature code has a spec", two modes, full spec loop, verification gates).
3. [x] Decided: **advisory** for the hackathon. An advisory nudge hook lives at
   `.kiro/hooks/spec-nudge.json` (asks on feature-sized work without a spec;
   does not hard-block).
4. [x] **Grilled the product** with `/grill-with-docs` → `GLOSSARY.md` and
   `docs/adr/0001-0003`.
5. [x] **Planned the feature split** into five specs (see README "Planned
   specs").
6. [x] **All five specs drafted** end to end (requirements → design → tasks)
   under `.kiro/specs/`: #1 `accounts`, #2 `paper-search`,
   #3 `reproducibility-scoring`, #4 `code-generation`, #5 `writer-workspace`.
   `paper-search` + `reproducibility-scoring` came in via `main` (merged into
   this branch); `writer-workspace` was grilled with `/grill-with-docs` →
   ADR-0005, ADR-0006, and four new glossary terms.

## Implementation status

All five specs are drafted. Build order was `accounts` → `paper-search` (stubbed
repro) → `reproducibility-scoring` (unstub) → `code-generation` →
`writer-workspace`. ADRs run `docs/adr/0001..0006`. Status below reflects what is
merged to `main`.

- [x] **#1 `accounts`** — backend auth (register/login/logout/session), frontend,
  and business logic merged (PRs #5, #10, #14). Only the manual-frontend
  final-checkpoint task is unchecked.
- [x] **#2 `paper-search`** — backend search/scoring/source adapters, frontend,
  and business logic merged (PRs #6, #11, #14). Reproducibility shipped stubbed
  behind the `score_reproducibility(paper_id)` seam, then unstubbed by #3. Only
  the manual-frontend final-checkpoint task is unchecked.
- [x] **#3 `reproducibility-scoring`** — scoring seam, scorers, and GitHub
  inspector merged (PRs #7, #12, #15); unstubs the paper-search seam at the same
  signature. Only the manual-frontend final-checkpoint task is unchecked.
- [x] **#4 `code-generation`** — frontend (`Codegen_UI`, PR #8), the
  `Generation_Helper` / `Scoring_Helper` business logic (`core/codegen.py`,
  PR #15), and the full backend — `GenerationJob`/`Generation` tables +
  migration, async job worker, `Codegen_API` router — are merged (PR #13).
  Post-prototype hardening (robust delimiter parsing, mock mode, job **cancel**;
  R9–R11) is in **open PR #19** (`fix/codegen-parse-cancel-mock`), suite green.
  The `writer` case is still stubbed (see Deferred). Manual final-checkpoint
  tasks (8, 12) unchecked.
- [x] **#5 `writer-workspace`** — frontend (`Writer_UI`, PR #9), the
  `Extraction_Helper` (`core/extraction.py`, PR #16), **and the backend
  persistence + `Writer_API`** (`PaperClaim`/`WriterManuscript`/
  `WriterSourceFile` tables + migration, claim/manuscript/source endpoints,
  router wiring) are merged (PR #17). Claim → upload manuscript/source →
  list/delete all work (verified via API + UI). Remaining: 7 optional (`*`) test
  tasks (1.5, 3.3, 5.6–5.11) — the `/api/writer/*` surface has no dedicated
  coverage yet.

See `summary-1st-prototype.md` for the full first-prototype handoff (verified
flows, what's left, operational gotchas).

## Deferred

- **code-generation `writer` case is intentionally not wired yet.** The three
  generation cases are `generate` (Reader, no repo), `align` (Reader, has repo),
  and `writer` (Writer, from their uploaded manuscript + source). `generate` and
  `align` work end to end. The `writer` case needs a Writer's **persisted upload**
  — which **now exists** (writer-workspace shipped `WriterManuscript` /
  `WriterSourceFile`, PR #17) — but `_precondition` in
  `backend/app/routers/codegen.py` (the `case is Case.writer` arm) was never
  wired to read it, so it still returns a `refused` job ("No uploaded manuscript
  for this paper yet…"). **To finish it (top-priority follow-up):** replace that
  stub arm with a lookup that loads the Writer's claim + manuscript/source for the
  paper and builds `GenerationInputs(manuscript_text=…, uploaded_source=…)`,
  refusing only when there genuinely is no upload; add a frontend trigger in the
  writer workspace. Touches backend + frontend; add it as a task on the
  code-generation spec (R5.3 already describes the behavior). Depends on PR #19.

## Follow-ups

- [x] **Rebased open PR #13 (`code-generation_backend`) onto current `main`** and
  merged. `cd backend && uv run pytest` → 124 passed.
- [ ] **Merge PR #19** (`fix/codegen-parse-cancel-mock`) — generation parse fix,
  mock mode, job cancel. After merge: `docker compose up -d --build backend` so
  the `cancelled` enum migration applies (`alembic/` is not compose-watch-synced).
- [ ] **Wire the code-generation `writer` case** to the persisted Writer uploads
  (see Deferred) — the single most important remaining feature gap.
- [ ] **writer-workspace tests:** `/api/writer/*` has no dedicated coverage; do at
  least optional tasks 3.3 (migration smoke) and 5.11 (API edge + mocked
  Git-fetch).
- [ ] Manual-frontend final-checkpoint tasks remain unchecked for `accounts`,
  `paper-search`, `reproducibility-scoring`, and `code-generation` (tasks 8/10/12)
  — verify each in the browser and tick the final task in its `tasks.md`.
- [ ] **Rotate the leaked AWS key** `AKIA6HF7RX3XVOANFSIE` still present in `.env`.

## The workflow (for reference)

Litmus test for where information goes — *"Will this still be true after this
feature ships?"* Yes → steering. This feature only → spec.

**Per feature:**
1. `/grill-with-docs` — interrogate until the design tree is empty; capture
   glossary terms + ADRs.
2. `/spec new <feature>` — pour the grilled understanding into `requirements.md`.
3. Review requirements → `design.md` → `tasks.md` (use `frontend-design` for UI).
4. `/spec run <feature>` — implement with `ponytail` on to keep changes minimal.
5. Promote anything durable back into steering / an ADR.

**Scale it:** big/unclear feature → full loop; small/obvious change → skip to a
Quick Spec or just implement with ponytail. Don't grill a one-line change.

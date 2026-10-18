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
  R9–R11) merged (PR #19). The `writer` case is now **wired end to end**
  (spec Task 13 — `_precondition` resolves the Writer's persisted claim +
  manuscript/source; writer-workspace has a Generate trigger), suite green
  (132 passed). Manual final-checkpoint tasks (8, 12) unchecked.
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

- (none open) — the code-generation `writer` case, previously the top deferral,
  is now wired (spec Task 13): `_precondition` in
  `backend/app/routers/codegen.py` resolves the Writer's claim +
  manuscript/source and builds `GenerationInputs`, refusing only when there is
  genuinely no upload; the writer workspace has a Generate trigger.

## Follow-ups

- [x] **Rebased open PR #13 (`code-generation_backend`) onto current `main`** and
  merged. `cd backend && uv run pytest` → 124 passed.
- [x] **Merge PR #19** (`fix/codegen-parse-cancel-mock`) — generation parse fix,
  mock mode, job cancel. Merged; `cancelled` enum migration applied.
- [x] **Wire the code-generation `writer` case** to the persisted Writer uploads
  (spec Task 13). `_precondition` resolves claim + manuscript/source; writer
  workspace has a Generate trigger. Verified in the browser.
- [ ] **writer-workspace tests:** `/api/writer/*` has no dedicated coverage; do at
  least optional tasks 3.3 (migration smoke) and 5.11 (API edge + mocked
  Git-fetch).
- [ ] Manual-frontend final-checkpoint tasks remain unchecked for `accounts`,
  `paper-search`, `reproducibility-scoring`, and `code-generation` (tasks 8/10/12)
  — verify each in the browser and tick the final task in its `tasks.md`.
- [ ] **Score dimension descriptions (business logic → frontend):** the frontend
  shows an info (ⓘ) tooltip on every score — Relevance, Reproducibility, Overall,
  Code quality, Setup completeness — but the copy is a **placeholder** (see the
  `HINTS` map in `frontend/src/components/ScoreBar.tsx`, each tagged "(Final copy
  pending.)"). Business logic/product needs to define the real, agreed
  description for each dimension (what it measures, how it's computed); then
  swap them into that one `HINTS` map.
- [ ] **Reproducibility explanation is too generic (backend / business logic):**
  the "How the reproducibility score was reached" explanation is produced by
  `Score_Explainer` in `backend/app/services/repro/explainer.py`. Its prompt
  only feeds coarse boolean repo signals (`has_readme`, `has_license`,
  `has_tests`, `recent_activity`, `exists`, `inspectable`) plus the number and
  setup completeness — so the output is unavoidably generic ("add a README, add
  a license, add tests…") and tells the reader nothing specific about *this*
  paper. The richer `StandardResult` now exists (per-`Criterion` results with
  status/evidence_note/category/weight, the seven `CategoryScore`s with
  `points_lost`, and the `discrepancies`) but is **not** passed to `explain()`.
  Action: extend `explain()` (and its caller in
  `backend/app/services/reproducibility.py`) to feed the top points-lost
  categories, the specific unmet/partial criteria with their evidence notes, and
  any paper-to-code discrepancies, so the explanation is specific and
  actionable. The frontend already renders the returned Markdown (headings
  stripped) and needs no further change once the copy improves. Keep the
  "score is fixed, never recompute" guard (R5.2) and the no-LLM-on-roll-up rule
  (ADR-0009).
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

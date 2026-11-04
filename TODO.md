# TODO

## Project context + spec workflow — DONE (Phase 0 + first feature grilled)

**Status:** The foundation steering files are complete and the product has been
grilled into shared understanding. All five feature specs are drafted
(`accounts`, `paper-search`, `reproducibility-scoring`, `code-generation`,
`writer-workspace`). Implementation is well underway — see "Implementation
status" below.

Done:

1. **Foundation steering** (now consolidated into `CLAUDE.md`, always loaded):
   - [x] `product.md` — filled in; corrected for the Writer-content storage
     exception (see `docs/adr/0003`).
   - [x] `tech.md` — filled in; the four "to decide" items (data sources, LLM
     provider, auth, secrets) are now settled and recorded as ADRs.
   - [x] `structure.md` — conventions confirmed (`routers/` for API routes,
     `models/` for tables, `components/` for frontend).
2. [x] **A `workflow.md` steering file** encoding the dev loop (litmus test,
   "feature code has a spec", two modes, full spec loop, verification gates).
3. [x] Decided: **advisory** for the hackathon. The rule "ask before starting
   feature-sized work without a spec" lives in `CLAUDE.md` (it was a Kiro hook,
   `spec-nudge.json`, until the move to Claude Code); it does not hard-block.
4. [x] **Grilled the product** with `/grill-with-docs` → `GLOSSARY.md` and
   `docs/adr/0001-0003`.
5. [x] **Planned the feature split** into five specs (see README "Planned
   specs").
6. [x] **All five specs drafted** end to end (requirements → design → tasks)
   under `specs/`: #1 `accounts`, #2 `paper-search`,
   #3 `reproducibility-scoring`, #4 `code-generation`, #5 `writer-workspace`.
   `paper-search` + `reproducibility-scoring` came in via `main` (merged into
   this branch); `writer-workspace` was grilled with `/grill-with-docs` →
   ADR-0005, ADR-0006, and four new glossary terms.

> **Tooling note.** The prototype was built in Kiro. The repo now targets Claude
> Code: steering is `CLAUDE.md`, specs moved `.kiro/specs/` → `specs/`, the
> workflow is the `/spec` skill (`new` / `run` / `status`), and Kiro-only files
> (`.config.kiro`, `tasks.meta.json`, the hook) were dropped. The Kiro layout
> remains in git history on `main`.

## Implementation status

All five specs are drafted. Build order was `accounts` → `paper-search` (stubbed
repro) → `reproducibility-scoring` (unstub) → `code-generation` →
`writer-workspace`. ADRs run `docs/adr/0001..0010`. Status below reflects what is
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

- [ ] **#6 `demo-mode`** (branch `demo/deterministic-search`, not on `main`) —
  record/replay Cassette at the Source, LLM and GitHub seams, inline scoring and
  deterministic ordering, demo scripts and `demo/SCRIPT.md` (ADR 0010). Tasks 1–9.1
  done; remaining: **9.2 manual rehearsal** (record the real query, commit the
  Cassette, replay with network/AWS off, check *Final score* doesn't reorder).

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
- [x] **Manual-frontend final checkpoints verified in the browser** for
  `accounts`, `paper-search`, `reproducibility-scoring`, and `code-generation`
  (tasks 8/10/12). Frontend for this iteration is complete and merged (search
  UX, writer wording, mode headings/persistence, landing hero, accessibility
  tiers 1–3, AuthBar, score labels + tooltips, and the Standards-Conformance
  breakdown + review-report rendering). Still tick the matching final task in
  each spec's own `tasks.md` if not already done.
- [ ] **Score dimension descriptions (business logic → frontend):** the frontend
  shows an info (ⓘ) tooltip on every score — Relevance, Reproducibility, Overall,
  Code quality, Setup completeness — but the copy is a **placeholder** (see the
  `HINTS` map in `frontend/src/components/ScoreBar.tsx`, each tagged "(Final copy
  pending.)"). Business logic/product needs to define the real, agreed
  description for each dimension (what it measures, how it's computed); then
  swap them into that one `HINTS` map.
- [x] **Reproducibility explanation now specific (branch `backend-repro-explanation`).**
  `Score_Explainer` (`backend/app/services/repro/explainer.py`) previously saw
  only coarse boolean repo signals, so its prose was generic. `explain()` now
  takes the full `StandardResult` and builds the prompt from the top points-lost
  categories, the heaviest unmet/partial criteria with their evidence notes, and
  any paper-to-code discrepancies; the caller in
  `backend/app/services/reproducibility.py` passes it through. R5.2 (score fixed)
  and R5.3 (failure → no explanation) preserved; no LLM on the roll-up path
  (ADR-0009). Merged (PR #35) and verified in the browser — the explanation now
  names specific gaps. `test_repro_inspector.py` passed in-agent; the DB-backed
  seam tests still want a host `cd backend && uv run pytest` run for regression
  safety (testcontainers need host `uv`).
- [x] **Review/code generation no longer truncated (PR #36).** The `ChatBedrock`
  client in `backend/app/core/codegen.py` set no `max_tokens`, so long
  `REVIEW.md` reports (and generated code) hit Bedrock's low default and were
  cut off mid-output — the stored artifact itself was incomplete, not a display
  issue. Added `codegen_max_tokens` (default 8192, env `CODEGEN_MAX_TOKENS`,
  forwarded in `compose.yaml`) and passed it to the shared codegen `_client()`.
  Merged and verified in the browser (a freshly generated review renders in
  full). Codegen helper tests passed in-agent; same host-pytest caveat as above.
  Note: if a configured model's output ceiling is below 8192, lower
  `CODEGEN_MAX_TOKENS`.
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

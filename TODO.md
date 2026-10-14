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
- [~] **#4 `code-generation`** — frontend (`Codegen_UI`, PR #8) and the
  `Generation_Helper` / `Scoring_Helper` business logic (`core/codegen.py`,
  PR #15) are merged. The rest of the backend — `GenerationJob`/`Generation`
  tables + migration, the async job worker, and the `Codegen_API` router — is in
  **open PR #13** (`code-generation_backend`), now rebased onto current `main`
  (the duplicated helper dropped; the worker adapted to the merged helper's API)
  with the full suite green. Ready for review/merge.
- [~] **#5 `writer-workspace`** — frontend (`Writer_UI`, PR #9) and the
  `Extraction_Helper` business logic (`core/extraction.py`, PR #16) are merged.
  The persistence (Writer `Upload` model + migration), upload/claim endpoints,
  and wiring are **not implemented** (`.kiro/specs/writer-workspace/tasks.md`
  task 1 onward still open). Depends on `accounts`, `reproducibility-scoring`,
  `code-generation`.

## Deferred

- **code-generation `writer` case is intentionally not wired yet.** The three
  generation cases are `generate` (Reader, no repo), `align` (Reader, has repo),
  and `writer` (Writer, from their uploaded manuscript + source). `generate` and
  `align` work end to end because their inputs already exist (Experiment Setup,
  the Paper `repo_url`). The `writer` case needs a Writer's **persisted upload**
  (manuscript text + source code, per `docs/adr/0003`), and that `Upload` model
  does not exist yet — it belongs to **#5 `writer-workspace`**, which hasn't
  built persistence. Until it does, the `writer` case is handled by the normal
  precondition path: `POST /api/codegen/jobs` with `case=writer` returns a
  `refused` job with the reason "No uploaded manuscript for this paper yet, so
  there's nothing to generate from." No crash; the pipeline is ready. **To
  finish it later:** build the `writer-workspace` `Upload` persistence, then
  replace the stub branch in `backend/app/routers/codegen.py` `_precondition`
  (the `case is Case.writer` arm) with a lookup that loads the Writer's upload
  for the paper and only refuses when there genuinely isn't one.

## Follow-ups

- [x] **Rebased open PR #13 (`code-generation_backend`) onto current `main`.** It
  was branched before PR #15 merged `core/codegen.py` (the `Generation_Helper` /
  `Scoring_Helper`); both added that file. Resolved by dropping #13's copy of
  `core/codegen.py` and its helper test, keeping the merged version, and adapting
  the worker to the merged helper's API (`GenerationInputs.experiment_setup` is
  required; refusal paths now carry no inputs). `cd backend && uv run pytest` →
  124 passed.
- [ ] Manual-frontend final-checkpoint tasks remain unchecked for `accounts`,
  `paper-search`, `reproducibility-scoring`, and `code-generation` — verify each
  in the browser and tick the final task in its `tasks.md`.

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

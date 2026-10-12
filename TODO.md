# TODO

## Project context + spec workflow — DONE (Phase 0 + first feature grilled)

**Status:** The foundation steering files are complete and the product has been
grilled into shared understanding. Three feature specs are drafted (`accounts`,
`code-generation`, `writer-workspace`); none implemented yet.

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
6. [x] **Specs #1 `accounts`, #4 `code-generation`, #5 `writer-workspace`**
   drafted end to end (requirements → design → tasks) under `.kiro/specs/`.
   `writer-workspace` was grilled with `/grill-with-docs` → ADR-0005, ADR-0006,
   and four new glossary terms.

## Next

**Specs drafted so far** (requirements → design → tasks, under `.kiro/specs/`):
`accounts`, `code-generation`, `writer-workspace`. **Still to spec:**
`paper-search`, `reproducibility-scoring`. None implemented yet. ADRs now run
`docs/adr/0001..0006`.

Note: specs were drafted out of dependency order — `code-generation` and
`writer-workspace` are drafted ahead of the `paper-search`/`reproducibility-scoring`
inputs they consume. Each stands on documented assumptions (code-generation
*consumes* the Experiment Setup + repro score; writer-workspace *produces* the
persisted Writer uploads), so implement in the build order below.

- [ ] Implement the `accounts` tasks (`.kiro/specs/accounts/tasks.md`).
- [ ] Spec #2 `paper-search` — `/spec new paper-search` (can stub the
  reproducibility score behind a `score_reproducibility(paper_id)` seam to ship
  search first).
- [ ] Spec #3 `reproducibility-scoring` — `/spec new reproducibility-scoring`
  (GitHub-only first iteration; unstubs the `paper-search` seam at the same
  signature).
- [x] Spec #4 `code-generation` drafted (`.kiro/specs/code-generation/`).
- [x] Spec #5 `writer-workspace` drafted (`.kiro/specs/writer-workspace/`),
  grilled with `/grill-with-docs`: decisions captured in `GLOSSARY.md` (Paper
  Claim, Paper Reference, Writer Manuscript, Writer Source File) and two ADRs —
  `docs/adr/0005` (upload ingestion is synchronous) and `docs/adr/0006` (public
  Git fetched as an HTTP codeload tarball, not cloned). Source is text-only
  (binaries skipped); claims de-dupe per identifier scheme.

**Build order** (implement in this order regardless of draft order):
`accounts` → `paper-search` (stubbed repro) → `reproducibility-scoring` (unstub)
→ `code-generation` → `writer-workspace`.

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

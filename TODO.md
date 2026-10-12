# TODO

## Project context + spec workflow — DONE (Phase 0 + first feature grilled)

**Status:** The foundation steering files are complete and the product has been
grilled into shared understanding. All five feature specs are drafted
(`accounts`, `paper-search`, `reproducibility-scoring`, `code-generation`,
`writer-workspace`); none implemented yet.

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

## Next

All five specs are drafted; the remaining work is **implementation**, in the
build order below (the specs were drafted out of dependency order). ADRs now run
`docs/adr/0001..0006`.

- [ ] Implement **#1 `accounts`** (`.kiro/specs/accounts/tasks.md`) — no deps.
- [ ] Implement **#2 `paper-search`** — stub reproducibility behind the
  `score_reproducibility(paper_id)` seam so search ships first.
- [ ] Implement **#3 `reproducibility-scoring`** — GitHub-only first iteration;
  unstubs the `paper-search` seam at the same signature.
- [ ] Implement **#4 `code-generation`** — consumes the Experiment Setup + repro
  score (ADR-0004: generated code never feeds a Paper's repro score).
- [ ] Implement **#5 `writer-workspace`** — depends on `accounts`,
  `reproducibility-scoring`, `code-generation`.

**Build order:** `accounts` → `paper-search` (stubbed repro) →
`reproducibility-scoring` (unstub) → `code-generation` → `writer-workspace`.

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

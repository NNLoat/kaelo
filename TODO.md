# TODO

## Project context + spec workflow — DONE (Phase 0 + first feature grilled)

**Status:** The foundation steering files are complete and the product has been
grilled into shared understanding. The first feature spec (`accounts`) exists.

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
6. [x] **Spec #1 `accounts`** drafted end to end (requirements → design →
   tasks) under `.kiro/specs/accounts/`.

## Next

Specs drafted so far: `accounts`, `paper-search`, `reproducibility-scoring`
(requirements → design → tasks, under `.kiro/specs/`). None implemented yet.

- [ ] Implement the `accounts` tasks (`.kiro/specs/accounts/tasks.md`).
- [x] Draft spec #2 `paper-search` (`.kiro/specs/paper-search/`) — reproducibility
  stubbed behind a `score_reproducibility(paper_id)` seam so search ships first.
- [ ] Implement the `paper-search` tasks.
- [x] Draft spec #3 `reproducibility-scoring` (`.kiro/specs/reproducibility-scoring/`)
  — GitHub-only first iteration; unstubs the `paper-search` seam. Aligned with
  `paper-search` on the `experiment_setup` mirror and the additive
  `reproducibility_breakdown` detail field.
- [ ] Implement the `reproducibility-scoring` tasks (after `paper-search`).
- [ ] Spec #4 `code-generation`, then #5 `writer-workspace` — run
  `/spec new <name>` per the build order in the README.

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

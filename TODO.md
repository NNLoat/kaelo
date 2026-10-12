# TODO

## Define the team steering + spec workflow (do together with the team)

**Status:** `workflow.md` and the foundation steering files now exist. `product.md`,
`tech.md`, and `structure.md` are **stubs** — `tech.md`/`structure.md` are seeded
from the README/repo, `product.md` is blank. Fill them in together.

Done:

1. **Foundation steering files** in `.kiro/steering/` (always-included):
   - [ ] `product.md` — created as a **stub**; fill in with the team.
   - [ ] `tech.md` — created, **seeded** from the README; confirm + expand.
   - [ ] `structure.md` — created, **seeded** from the repo; confirm conventions.
2. [x] **A `workflow.md` steering file** encoding the dev loop (litmus test,
   "feature code has a spec", two modes, full spec loop, verification gates).
3. [x] Decided: **advisory** for the hackathon. An advisory nudge hook lives at
   `.kiro/hooks/spec-nudge.json` (asks on feature-sized work without a spec;
   does not hard-block).

### The workflow we sketched (to formalize later)

Litmus test for where information goes — *"Will this still be true after this
feature ships?"* Yes → steering. This feature only → spec.

**Phase 0 — once, at project start:** create the three foundation steering files.

**Phase 1 — per feature:**
1. `/grill-with-docs` — interrogate until the design tree is empty; capture
   glossary terms + ADRs.
2. `/spec new <feature>` — pour the grilled understanding into `requirements.md`.
3. Review requirements → `design.md` → `tasks.md` (use `frontend-design` for UI).
4. `/spec run <feature>` — implement with `ponytail` on to keep changes minimal.
5. Promote anything durable back into steering / an ADR.

**Scale it:** big/unclear feature → full loop; small/obvious change → skip to a
Quick Spec or just implement with ponytail. Don't grill a one-line change.

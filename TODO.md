# TODO

## Define the team steering + spec workflow (do together with the team)

Deferred on purpose: we want to build out each phase *with* the whole team so
everyone shares the same mental model, rather than one person authoring it.

When we sit down together, create:

1. **Foundation steering files** in `.kiro/steering/` (always-included):
   - `product.md` — what we're building, for whom, core objectives.
   - `tech.md` — stack + hard constraints (FastAPI/SQLModel/Postgres,
     Vite/React/Tailwind, Alembic for migrations, testcontainers for tests,
     pnpm pinned).
   - `structure.md` — repo layout, naming, where things go.
2. **A `workflow.md` steering file** that encodes our dev loop so every
   teammate's agent nudges them through it.
3. Decide: advisory-only, or add a hook that enforces "feature code has a spec".
   (Leaning advisory-only for the hackathon.)

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

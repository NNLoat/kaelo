# Workflow

How we develop on this project. This file is always included so every teammate's
agent nudges them through the same loop. The workflow is a tool, not a gate —
scale the ceremony to the change (see below).

## The litmus test (steering vs. spec)

Before writing anything down, ask:

> **"Will this still be true after this feature ships?"**

- **Yes** → it's a durable, project-wide rule → put it in **steering** (this
  directory) or an **ADR**.
- **No, it's only true for this feature** → it belongs in that feature's **spec**.

Use the same test *after* implementing to decide what to **promote** back into
steering / an ADR.

## Rule: feature code has a spec

**Feature work must have a spec.** A change is feature work if it:

- impacts a **functional requirement** or **user story**, or
- introduces a **breaking change** (e.g. database handling / schema, a changed
  public API contract).

If neither is true, it is **not** feature work — just implement it with the
`ponytail` skill. Don't manufacture a spec for a typo, copy tweak, or one-file fix.

This is advisory for the hackathon: a hook (`.kiro/hooks/spec-nudge.json`) will
*ask* when a change looks feature-sized without a spec. It nudges — it does not
hard-block.

## Two modes

| The change… | Mode |
| --- | --- |
| No functional-requirement / user-story impact **and** no breaking change | **Just implement with `ponytail`** |
| Touches a functional requirement / user story, **or** is a breaking change (DB handling, schema, public contract) | **Full spec loop** |

When unsure which mode applies, say so and ask — don't guess.

## Full spec loop (per feature)

1. **`/grill-with-docs`** — interrogate the feature until the design tree is
   empty. Capture glossary terms and ADRs *as you go*; don't skip that capture.
2. **`/spec new <feature>`** — pour the grilled understanding into
   `requirements.md`.
3. Review `requirements.md` → `design.md` → `tasks.md`. Use the
   **`frontend-design`** skill for any UI.
4. **`/spec run <feature>`** — implement with **`ponytail`** on to keep changes
   minimal.
5. **Promote** anything durable (passes the litmus test) back into steering or
   an ADR.

If requirements are already crisp, grilling is optional — go straight to
`/spec new`. If a term keeps being ambiguous across the team, use
**`domain-modeling`** → `GLOSSARY.md`.

## Verification gates (before "done")

- **Backend:** `cd backend && uv run pytest` must pass. See
  `backend/README.md` for how tests are wired (testcontainers; run on the host).
- **Schema changes:** generate and review an Alembic migration —
  `docker compose exec backend uv run alembic revision --autogenerate -m "..."`.
  Autogenerate is a draft; review it. Commit migrations under `alembic/versions/`.
- **Frontend:** **no automated test gate** — the team tests the UI manually.
  Don't block on or invent a frontend test suite.

## Anti-patterns

- Don't grill a one-line change. The workflow is a tool, not a gate.
- Don't invent requirements — if something is unclear, ask.
- Don't skip glossary / ADR capture during grilling.

## See also

- `product.md` — what we're building and for whom.
- `tech.md` — stack and hard constraints.
- `structure.md` — repo layout and naming.
- `.kiro/skills/SKILLS.md` — the shared skills (`grill-with-docs`, `grilling`,
  `domain-modeling`, `ponytail`, `frontend-design`) and how to invoke them.

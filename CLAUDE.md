# Kaelo

An AI-assisted search engine for scientific papers that advances **open science**:
it finds papers, scores their reproducibility, and helps close the gap when a
paper ships without usable code. Built for researchers (not reviewers) in two
roles that share one account:

- **Reader** — finds, reads, and evaluates others' papers (search, reproducibility
  and code-quality scoring, opt-in code generation for papers with no repo).
- **Writer** — evaluates their own paper (scoring, code audit/generation).

Vocabulary lives in `GLOSSARY.md`; hard-to-reverse decisions in `docs/adr/`;
feature specs in `specs/`. Read the glossary before naming anything new.

## Out of scope

- Hosting full-text papers or repos **from search/indexed sources** — store only
  index/links. **Exception:** a Writer's own uploaded manuscript text and source
  *are* stored (ADR-0003).
- A general web search engine (scientific papers only).
- Executing generated code to verify it works.
- A peer-review/publishing platform.

## Stack

| Layer     | Tech                                              |
| --------- | ------------------------------------------------- |
| Backend   | FastAPI, SQLModel (sync psycopg), uv, Python 3.13 |
| Frontend  | Vite, React, TypeScript, Tailwind v4, pnpm        |
| Database  | postgres:17                                       |
| Dev infra | Docker Compose (compose watch)                    |

Hard constraints:

- **Migrations:** Alembic, never `create_all`. Commit under `backend/alembic/versions/`.
- **Package managers:** `uv` (backend), `pnpm` (frontend). Don't add others.
- **Local dev:** everything runs in containers (`docker compose up --watch`).
- **Versions:** pin to the stack above; latest stable patch within those majors.
- **Secrets:** env only (`.env`, gitignored). `.env.example` carries placeholders.

Settled decisions (ADRs under `docs/adr/`): OpenAlex + arXiv as sources, CS and
Medicine only (0001); LLM via Amazon Bedrock through LangChain, called from the
backend (0002); Writer uploads persisted (0003); generated code never feeds a
Paper's reproducibility score (0004); synchronous upload ingestion (0005); Git
URLs fetched as codeload tarballs (0006); domain captured at ingestion (0007);
reproducibility standard adapter (0008); LLM supplies evidence, the score roll-up
is deterministic (0009). Auth is username + password with a signed HTTP-only
session cookie.

## Layout and conventions

```
backend/   app/{main.py,core/,db/,models/,routers/,services/}  alembic/  tests/
frontend/  src/{api/,components/,components/writer/}
specs/     <feature>/{requirements,design,tasks}.md
docs/adr/  architecture decision records
.claude/   skills (committed); see .claude/skills/SKILLS.md
```

- Backend models in `backend/app/models/`; API routes in `backend/app/routers/`,
  registered in `main.py`; frontend components in `frontend/src/components/`.
- Follow standard Python and React naming.

## Verification gates (before "done")

- **Backend:** `cd backend && uv run pytest` must pass (testcontainers; run on the
  host, see `backend/README.md`). LLM and external Sources are mocked in tests,
  never called live.
- **Schema changes:** generate and review an Alembic migration:
  `docker compose exec backend uv run alembic revision --autogenerate -m "..."`.
  Autogenerate is a draft. After a migration, rebuild the backend image
  (`docker compose up -d --build backend`); `alembic/` is not compose-watch-synced.
- **Frontend:** `cd frontend && pnpm lint` (`tsc --noEmit`) is the only automated
  gate. The team tests the UI manually; don't invent a frontend test suite.

## Workflow

The workflow is a tool, not a gate. Scale the ceremony to the change.

**Litmus test (steering vs. spec):** *"Will this still be true after this feature
ships?"* Yes → project-wide rule (this file or an ADR). No → it belongs in that
feature's spec. Apply it again after implementing to decide what to promote.

**Feature work must have a spec.** A change is feature work if it impacts a
functional requirement or user story, or is a breaking change (DB schema, a
changed public API contract). Otherwise — typo, copy tweak, one-file fix — just
implement it with the `ponytail` skill; don't manufacture a spec. If the user asks
for something that looks feature-sized and no spec exists, ask once whether to
start with `/grill-with-docs` or `/spec new` before implementing. When unsure
which mode applies, say so and ask.

**Full loop (per feature):**

1. `/grill-with-docs` — interrogate the feature until the design tree is empty;
   capture glossary terms and ADRs as you go.
2. `/spec new <feature>` — pour the grilled understanding into `requirements.md`,
   then `design.md` and `tasks.md` (one approval gate between each).
3. `/frontend-design` for any UI.
4. `/spec run <feature> [task]` — implement tasks with `ponytail` on.
5. Promote anything durable into this file or an ADR.

If requirements are already crisp, skip grilling. If a term is ambiguous, use
`/domain-modeling` → `GLOSSARY.md`.

**Anti-patterns:** don't grill a one-line change; don't invent requirements (ask);
don't skip glossary/ADR capture while grilling.

## Skills

`grilling`, `grill-with-docs`, `domain-modeling`, `frontend-design`, and `spec`
are committed under `.claude/skills/`. `ponytail` comes from the `ponytail`
plugin (`/plugin install ponytail@ponytail`); the playwright MCP server is
configured in `.mcp.json`.

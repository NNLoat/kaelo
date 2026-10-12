# Tech

## Stack

| Layer     | Tech                                              |
| --------- | ------------------------------------------------- |
| Backend   | FastAPI, SQLModel (sync psycopg), uv, Python 3.13 |
| Frontend  | Vite, React, TypeScript, Tailwind v4, pnpm        |
| Database  | postgres:17                                       |
| Dev infra | Docker Compose (compose watch)                    |

## Hard constraints

- **Migrations:** Alembic, not `create_all`. Commit under `backend/alembic/versions/`.
- **Package managers:** `uv` (backend), `pnpm` (frontend) — pinned; don't add others.
- **Local dev:** everything runs in containers (`docker compose up --watch`); host needs only Docker.
- **Versions:** pin to the stack above; use the latest stable patch within those majors.

## To decide here (team)

Critical choices that outlive any one feature — settle them in this file:

- **Paper data source** — which index/API feeds search (e.g. OpenAlex, Semantic
  Scholar, arXiv)? We store only index/links, not full text (see `product.md`).
- **AI/LLM provider** — model + provider for search assist, scoring, and code generation.
- **Auth** — do Reader/Writer accounts need login? If so, what provider.
- **Secrets** — all config via env (`.env`), never committed.

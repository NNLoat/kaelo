# Tech

> **STUB — fill in with the team.** Seeded from the README; confirm and expand
> hard constraints together.

## Stack

| Layer     | Tech                                              |
| --------- | ------------------------------------------------- |
| Backend   | FastAPI, SQLModel (sync psycopg), uv, Python 3.13 |
| Frontend  | Vite, React, TypeScript, Tailwind v4, pnpm        |
| Database  | postgres:17                                       |
| Dev infra | Docker Compose (compose watch)                    |

## Hard constraints

- **Migrations:** Alembic, **not** `create_all`. Commit migrations under
  `backend/alembic/versions/`.
- **Backend tests:** testcontainers against a real throwaway `postgres:17`, run
  on the host via `uv run pytest`.
- **Package managers:** `uv` (backend) and `pnpm` (frontend) — pinned. Don't
  introduce others.
- **Local dev:** everything runs in containers (`docker compose up --watch`);
  the host needs only Docker.

## Add constraints here

- _e.g. supported Python/Node versions, lint/format tools, forbidden deps._

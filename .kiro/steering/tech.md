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

## Settled team decisions

The critical, feature-outliving choices below were settled during the
`/grill-with-docs` session and recorded as ADRs under `docs/adr/`:

- **Paper data sources** — OpenAlex + arXiv, scoped to Computer Science and
  Medicine; results merged and de-duplicated into a unified `Paper`. We store
  only index/links for indexed Papers (see `product.md`).
  See `docs/adr/0001-paper-data-sources-openalex-and-arxiv.md`.
- **AI/LLM provider** — Amazon Bedrock, accessed through LangChain, called from
  the backend, for search assist, scoring, and code generation.
  See `docs/adr/0002-llm-via-bedrock-and-langchain.md`.
- **Auth** — lightweight username + password accounts (one `User`; Reader and
  Writer are modes available to every account, not separate account types).
  Session via a signed, HTTP-only cookie (no broker/store in the stack). See the
  `accounts` spec under `.kiro/specs/accounts/`.
- **Writer-owned content is persisted** — the one carve-out from the index-only
  rule: a Writer's uploaded manuscript text and source code are stored in
  Postgres. See `docs/adr/0003-writer-uploads-are-persisted.md`.

## Secrets

- All config via env (`.env`), never committed. `.env.example` carries
  placeholders only. New secrets (e.g. a session signing secret, Bedrock/AWS
  credentials) are documented in `.env.example` and supplied via `.env`.

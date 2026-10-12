# Structure

> **STUB — fill in with the team.** Seeded from the current repo layout; confirm
> naming conventions and "where things go" together.

## Repo layout

```
.
├── backend/            # FastAPI + SQLModel service
│   ├── app/
│   │   ├── main.py     # app factory, routes, lifespan
│   │   ├── core/       # settings
│   │   ├── db/         # engine + session
│   │   └── models/     # SQLModel tables
│   ├── alembic/        # migrations (versions/ committed)
│   └── tests/          # pytest + testcontainers
├── frontend/           # Vite + React + TS + Tailwind
│   └── src/
├── compose.yaml        # Docker Compose orchestration + watch
├── .kiro/
│   ├── steering/       # always-included team context (this file)
│   └── skills/         # vendored AI skills, shared via git
└── .env.example
```

## Conventions (fill in)

- **Where new backend models go:** `backend/app/models/`.
- **Where new API routes go:** _decide + document._
- **Where new frontend components go:** _decide + document._
- **Naming:** _files, components, DB tables, etc._

# Structure

Follow mainstream best practice for each stack so the layout stays predictable
and easy to debug.

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
│   ├── steering/       # always-included team context
│   └── skills/         # vendored AI skills, shared via git
└── .env.example
```

## Conventions

- **Backend models:** `backend/app/models/`.
- **API routes:** `backend/app/routers/`, registered on the FastAPI app in `main.py`.
- **Frontend components:** `frontend/src/components/`.
- **Naming:** follow standard Python and React conventions.

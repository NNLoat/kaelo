# backend

FastAPI + SQLModel service managed with [uv](https://docs.astral.sh/uv/).

## Local (without Docker)

```bash
uv sync
uv run fastapi dev app/main.py
```

## Layout

```
app/
├── main.py          # app factory, lifespan, routes
├── core/config.py   # settings (pydantic-settings)
├── db/session.py    # engine + session dependency
└── models/item.py   # example SQLModel table
alembic/             # database migrations
├── env.py           # wired to app settings + SQLModel metadata
└── versions/        # migration scripts (committed to git)
alembic.ini
entrypoint.sh        # runs `alembic upgrade head`, then starts the server
```

## Database migrations (Alembic)

Schema is managed by Alembic, **not** `create_all`. The container entrypoint runs
`alembic upgrade head` on every boot before the server starts, so a fresh database
is brought up to the latest schema automatically.

### After you change a model

```bash
# generate a migration by diffing your models against the live dev DB
docker compose exec backend uv run alembic revision --autogenerate -m "describe change"

# review the generated file in alembic/versions/ — autogenerate is a draft,
# not infallible (e.g. it can't tell a rename from a drop+add)

# apply it (also happens automatically on next container start)
docker compose exec backend uv run alembic upgrade head
```

### Useful commands

```bash
docker compose exec backend uv run alembic current      # show applied revision
docker compose exec backend uv run alembic history       # list migrations
docker compose exec backend uv run alembic downgrade -1  # roll back one step
```

> Migration files under `alembic/versions/` are part of your source — commit them.
> They are copied into the image at build time, so after generating a brand-new
> migration you may need `docker compose build backend` once for it to land in the image
> (subsequent `up` runs pick it up automatically).

## Testing

Backend tests run against a **real, throwaway `postgres:17`** started by
[testcontainers](https://testcontainers.com/). The test database's lifecycle is
owned entirely by the test run — it is **never** part of, or triggered by, the
dev `compose.yaml`. `docker compose up` never runs tests.

```bash
cd backend
uv run pytest            # run everything
uv run pytest -v         # verbose
uv run pytest tests/test_items_api.py   # one file
```

Requirements:

- A reachable Docker daemon (the test runner spawns the Postgres container).
- Tests run on the **host** (`uv run pytest`), not inside the backend container.
  Running them in a container would require mounting the Docker socket.

How it's wired (`tests/conftest.py`):

- A session-scoped `postgres:17` container is started once per run.
- The schema is created with `create_all` for speed; Alembic migrations are
  exercised separately in `tests/test_migrations.py` (upgrade → downgrade → upgrade).
- Each test runs inside an outer transaction that is **rolled back** on teardown,
  so tests are isolated and never leak state.
- The FastAPI `get_session` dependency is overridden to use the test session, and
  the API is driven through `TestClient`.

> Note: `TESTCONTAINERS_RYUK_DISABLED=true` is set in `conftest.py`. The Ryuk
> reaper sidecar bind-mounts the Docker socket, which some runtimes (e.g. Colima
> on macOS) reject. Cleanup is handled by `with PostgresContainer(...)` context
> managers instead.

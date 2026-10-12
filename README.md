# muit-hackathon

Full-stack infrastructure template.

| Layer     | Tech                                              |
| --------- | ------------------------------------------------- |
| Backend   | FastAPI, SQLModel (sync psycopg), uv, Python 3.13 |
| Frontend  | Vite, React, TypeScript, Tailwind v4, pnpm        |
| Database  | postgres:17                                       |
| Dev infra | Docker Compose (compose watch)                    |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Compose v2 (`docker compose version` should report v2.22+ for `watch` support)

That's it — everything runs inside containers for local development. You do **not** need Python, Node, uv, or pnpm installed on the host.

## Quick start

```bash
# copy env defaults
cp .env.example .env

# build and start everything with live-reload
docker compose up --watch
```

Services:

| Service    | URL                            |
| ---------- | ------------------------------ |
| Frontend   | http://localhost:5173          |
| Backend    | http://localhost:8000          |
| API docs   | http://localhost:8000/docs     |
| Postgres   | localhost:5432                 |

`docker compose up --watch` enables [Compose Watch](https://docs.docker.com/compose/how-tos/file-watch/):
edits to backend or frontend source are synced into the running containers and both dev
servers hot-reload. Dependency manifest changes (`pyproject.toml`, `package.json`) trigger
an automatic image rebuild.

## Working on this project

### First-time setup (once per machine)

1. Install [Docker](https://docs.docker.com/get-docker/) with Compose v2.22+.
2. Clone the repo. The shared Kiro skills under `.kiro/skills/` come with it — no
   per-machine install.
3. `cp .env.example .env`
4. `docker compose up --watch` — first run builds images and applies database
   migrations automatically.
5. Open a new Kiro session so it discovers the skills in `.kiro/skills/`.

> Not yet done (see [`TODO.md`](TODO.md)): the team will create the foundation
> steering files (`.kiro/steering/product.md`, `tech.md`, `structure.md`) and a
> `workflow.md` together. Until then, there is no shared steering baseline.

### Developing a feature

The per-feature loop (to be formalized with the team — see [`TODO.md`](TODO.md)):

1. **Grill the requirements.** Run `/grill-with-docs` to interrogate the feature
   until it's fully understood; it captures glossary terms and ADRs as you go.
2. **Create a spec.** `/spec new <feature>` and pour the grilled understanding
   into `requirements.md`, then review `design.md` and `tasks.md`. Use the
   `frontend-design` skill for any UI.
3. **Implement.** `/spec run <feature>`, with the `ponytail` skill on to keep
   changes minimal.
4. **Verify.** Backend changes: `cd backend && uv run pytest`. Schema changes:
   generate a migration (see `backend/README.md`).
5. **Promote durable decisions** (project-wide rules, not feature-specific) into
   steering or an ADR.

Scale the ceremony: a big or unclear feature gets the full loop; a small, obvious
change can skip straight to implementation. Don't grill a one-line fix.

### When to use which — quick reference

| Situation | Use |
| --- | --- |
| Setting up the project's baseline (stack, structure, conventions) | **Steering** (`product.md` / `tech.md` / `structure.md`) |
| Starting a new feature, requirements are fuzzy | **`/grill-with-docs`** → then `/spec new` |
| Starting a feature, requirements are already crisp | `/spec new` directly (grilling optional) |
| A term keeps being ambiguous across the team | **`domain-modeling`** → `GLOSSARY.md` |
| A hard-to-reverse architectural choice | **ADR** (via `domain-modeling`) |
| Implementing spec tasks | **`ponytail`** on |
| Building UI | **`frontend-design`** |
| A decision that outlives the feature | Promote to **steering** / ADR |

**Hackathon-pragmatic note.** Full ceremony every time will slow a hackathon
down. Scale it:

- Big/unclear feature → full loop (grill → spec → run).
- Small/obvious change → skip straight to a Quick Spec, or just implement with
  `ponytail`. Kiro supports a lightweight "Quick Spec" for exactly this.

Don't grill a one-line change. The workflow is a tool, not a gate.

## Project layout

```
.
├── backend/            # FastAPI + SQLModel service
│   ├── app/
│   │   ├── main.py     # app factory, routes, lifespan
│   │   ├── core/       # settings
│   │   ├── db/         # engine + session
│   │   └── models/     # SQLModel tables
│   ├── pyproject.toml  # uv-managed deps
│   └── Dockerfile
├── frontend/           # Vite + React + TS + Tailwind
│   ├── src/
│   ├── package.json    # pnpm-managed deps
│   └── Dockerfile
├── compose.yaml        # Docker Compose orchestration + watch config
├── scripts/
│   └── update-skills.sh  # refresh vendored Kiro skills from pinned commits
├── .kiro/
│   └── skills/         # vendored AI skills, shared via git (see below)
├── TODO.md             # deferred: team steering + spec workflow
└── .env.example
```

## Common commands

```bash
docker compose up --watch          # start with live-reload
docker compose up -d                # start detached (no watch)
docker compose down                 # stop and remove containers
docker compose down -v              # also drop the Postgres volume
docker compose logs -f backend      # tail backend logs
docker compose exec backend bash    # shell into the backend
docker compose exec db psql -U app  # psql into the database
```

## Backend without Docker (optional)

```bash
cd backend
uv sync
uv run fastapi dev app/main.py
```

## Frontend without Docker (optional)

```bash
cd frontend
pnpm install
pnpm dev
```
## Kiro skills

Shared AI skills live in `.kiro/skills/` and are **committed to the repo**, so
every teammate gets the identical set by cloning — no per-machine install, and
they load the same way in Kiro IDE and Kiro CLI. This also keeps everyone's
workflow aligned instead of each IDE setup producing divergent artifacts.

| Skill | Use it for | Invoke |
| --- | --- | --- |
| `grill-with-docs` | Relentless requirements interview that captures a glossary + ADRs as you go | `/grill-with-docs` |
| `grilling` | Stress-test a plan or decision in rounds of questions | `/grilling` |
| `domain-modeling` | Sharpen terminology, write `GLOSSARY.md` and ADRs | auto / `/domain-modeling` |
| `ponytail` | "Lazy senior dev" mode — smallest change that fully solves the task | `/ponytail` |
| `frontend-design` | Distinctive, non-templated UI design guidance | auto / `/frontend-design` |

Skills are discovered at the start of a Kiro session: start a new session after
pulling, then either invoke a skill directly with its `/name` or let the agent
match it automatically from your request.

### Vendoring and updates

These skills are **vendored** (copied in) rather than installed by a package
manager — see [`.kiro/skills/SKILLS.md`](.kiro/skills/SKILLS.md), which pins each
skill to the exact upstream commit it came from (that file is the "lockfile").

To check for upstream changes or update:

```bash
./scripts/update-skills.sh      # fetch pinned upstream copies, show how ours differ
```

The script never overwrites the vendored files — they carry Kiro-specific
adaptations. To update: bump the SHA in both `scripts/update-skills.sh` and
`.kiro/skills/SKILLS.md`, run the script, review the printed diffs, and
hand-apply any upstream changes worth taking.

> Note: `ponytail`'s slash commands (`/ponytail-review`, `/ponytail-audit`, …)
> are not available in Kiro, which only loads the always-on ruleset. The core
> `ponytail` skill works as documented above.

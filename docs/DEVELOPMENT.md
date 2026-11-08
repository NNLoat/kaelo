# Development guide

Everything you need to run, test and extend Kaelo locally. For the product overview, see the [README](../README.md).

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
2. Clone the repo. The shared skills under `.claude/skills/` come with it — no
   per-machine install. Install the `ponytail` plugin once
   (`/plugin install ponytail@ponytail`).
3. `cp .env.example .env`
4. `docker compose up --watch` — first run builds images and applies database
   migrations automatically.
5. Start Claude Code in the repo root so it loads `CLAUDE.md`, the skills in
   `.claude/skills/`, and the Playwright MCP server from `.mcp.json`.

> The project context (product, stack, layout, workflow, verification gates) is in
> [`CLAUDE.md`](../CLAUDE.md), which Claude Code loads every session.

### Developing a feature

The per-feature loop (formalized in [`CLAUDE.md`](../CLAUDE.md)):

1. **Grill the requirements.** Run `/grill-with-docs` to interrogate the feature
   until it's fully understood; it captures glossary terms and ADRs as you go.
2. **Create a spec.** `/spec new <feature>` (the `spec` skill) and pour the grilled understanding
   into `requirements.md`, then review `design.md` and `tasks.md`. Use the
   `frontend-design` skill for any UI.
3. **Implement.** `/spec run <feature> [task]`, with the `ponytail` skill on to keep
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
| Setting up the project's baseline (stack, structure, conventions) | **`CLAUDE.md`** |
| Starting a new feature, requirements are fuzzy | **`/grill-with-docs`** → then `/spec new` |
| Starting a feature, requirements are already crisp | `/spec new` directly (grilling optional) |
| A term keeps being ambiguous across the team | **`domain-modeling`** → `GLOSSARY.md` |
| A hard-to-reverse architectural choice | **ADR** (via `domain-modeling`) |
| Implementing spec tasks | **`ponytail`** on |
| Building UI | **`frontend-design`** |
| A decision that outlives the feature | Promote to **`CLAUDE.md`** / ADR |

**Hackathon-pragmatic note.** Full ceremony every time will slow a hackathon
down. Scale it:

- Big/unclear feature → full loop (grill → spec → run).
- Small/obvious change → skip straight to a Quick Spec, or just implement with
  `ponytail`. A small feature can have a short spec (only the essential
  requirements and tasks).

Don't grill a one-line change. The workflow is a tool, not a gate.

## Project layout

```
.
├── backend/              # FastAPI + SQLModel service (uv)
│   ├── app/
│   │   ├── core/         # settings, security, codegen helper, PDF/archive extraction
│   │   ├── models/       # SQLModel tables
│   │   ├── routers/      # auth, papers, codegen, writer
│   │   └── services/     # sources, ranking, repro scoring + standards, demo-mode seams
│   ├── alembic/          # migrations
│   └── tests/            # pytest + Hypothesis + testcontainers
├── frontend/             # Vite + React + TypeScript + Tailwind v4 (pnpm)
├── specs/                # per-feature requirements / design / tasks
├── docs/                 # ADRs, concept paper, screenshots, archive
├── demo/                 # recorded Cassette, demo scripts, pitch deck
├── scripts/              # demo-record / demo-reset, skill updates
├── compose.yaml          # Docker Compose + watch config
├── CLAUDE.md             # project context + workflow, loaded every session
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

## Demo mode

For a repeatable live demo, `DEMO_MODE` records the app's three outside-world calls
(OpenAlex/arXiv, Bedrock, GitHub) into a committed **Cassette** and replays them
later with no network or AWS access. Results are scored inline and ordered
deterministically, so the same query shows the same cards in the same order every
time. See `docs/adr/0010-demo-mode-records-and-replays-at-the-seams.md` and
`specs/demo-mode/`.

| Setting | Values | Notes |
| --- | --- | --- |
| `DEMO_MODE` | `off` (default), `record`, `replay` | `off` leaves the app untouched |
| `DEMO_CASSETTE_PATH` | default `/demo/fixtures/cassette.json` | `./demo` is bind-mounted at `/demo` |
| `QUERY_EXPANSION_ENABLED` | `true` (default) / `false` | `false` skips the LLM query rewrite |

```bash
scripts/demo-record.sh   # run demo/queries.txt live, write the Cassette, print the order
scripts/demo-reset.sh    # empty DB, DEMO_MODE=replay, demo account (demo / demo-password)
```

The scripts set `QUERY_EXPANSION_ENABLED=false` and `CODEGEN_MOCK=false` themselves.
`demo-record.sh` also runs the code-generation/review jobs listed in
`demo/generations.txt`, so replay can answer them.
Both run `docker compose down -v`, so they **wipe the local database**. The
presenter's walkthrough is in `demo/SCRIPT.md`.

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
## Claude Code skills

Shared AI skills live in `.claude/skills/` and are **committed to the repo**, so
a clone gets the identical set with no per-machine install. (The prototype was
built in Kiro; the Kiro layout is in git history on `main`.)

| Skill | Use it for | Invoke |
| --- | --- | --- |
| `spec` | Spec-driven feature development: draft and run `specs/<feature>/` | `/spec new\|run\|status` |
| `grill-with-docs` | Relentless requirements interview that captures a glossary + ADRs as you go | `/grill-with-docs` |
| `grilling` | Stress-test a plan or decision in rounds of questions | `/grilling` |
| `domain-modeling` | Sharpen terminology, write `GLOSSARY.md` and ADRs | auto / `/domain-modeling` |
| `frontend-design` | Distinctive, non-templated UI design guidance | auto / `/frontend-design` |
| `ponytail` (plugin) | "Lazy senior dev" mode, plus `/ponytail-review`, `/ponytail-audit` | `/ponytail` |

Skills load at the start of a session: start a new one after pulling, then
invoke a skill with its `/name` or let Claude match it from your request.

### Vendoring and updates

The vendored skills are copied in rather than installed by a package manager;
[`.claude/skills/SKILLS.md`](../.claude/skills/SKILLS.md) pins each to the upstream
commit it came from (that file is the "lockfile"):

```bash
./scripts/update-skills.sh      # fetch pinned upstream copies, show how ours differ
```

The script never overwrites the vendored files. To update: bump the SHA in both
`scripts/update-skills.sh` and `.claude/skills/SKILLS.md`, run the script, review
the printed diffs, and hand-apply any upstream changes worth taking.


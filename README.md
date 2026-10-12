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

> The team authored the foundation steering files in `.kiro/steering/`:
> `workflow.md` (the dev loop) is complete; `product.md`, `tech.md`, and
> `structure.md` exist as stubs to fill in together (see [`TODO.md`](TODO.md)).
> An advisory spec-nudge hook lives at `.kiro/hooks/spec-nudge.json`.

### Developing a feature

The per-feature loop (formalized in [`.kiro/steering/workflow.md`](.kiro/steering/workflow.md)):

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

## Planned specs

The product was grilled (`/grill-with-docs`) into shared understanding before any
spec was written. See `GLOSSARY.md` and `docs/adr/0001..0006` for the settled
vocabulary and decisions. The work is split into focused specs rather than one
mega-spec; build them in dependency order. **Not yet created** — run
`/spec new <name>` per feature when ready.

### Cross-cutting decisions (apply to every spec)

- **Sources:** OpenAlex + arXiv, scoped to Computer Science and Medicine; results
  merged and de-duplicated into a unified `Paper` (ADR-0001).
- **LLM:** Amazon Bedrock via LangChain, called from the backend (ADR-0002).
- **Writer-owned content is persisted** (manuscript text + source), the one
  carve-out from the index-only rule (ADR-0003). Reader/search side stays
  link-only.
- **Storage:** everything in Postgres (no S3/Redis); schema via Alembic.
- **Async work:** FastAPI `BackgroundTasks`, no broker.
- **Auth:** username + password; every `User` can use both Reader and Writer
  modes.

### Shared schema (via Alembic)

Core tables by spec: `User` (accounts); `Paper`, `ReproducibilityScore`,
`ExperimentSetup` (paper-search / reproducibility-scoring); `GenerationJob`,
`Generation` (code-generation); `PaperClaim`, `WriterManuscript`,
`WriterSourceFile` (writer-workspace). Writer content hangs off `PaperClaim`;
both Writer source files and generated artifacts are stored as (relative path,
content) rows / entries.

### Spec 1 — `accounts` (foundation)

Lightweight auth: username + password registration/login, session handling. One
account; both Reader and Writer modes available to it. Introduces the `User`
table.

- **Depends on:** nothing.
- **Blocks:** `writer-workspace` (needs `User` to own a `PaperClaim`).

### Spec 2 — `paper-search` (Reader entry point) — **drafted**

Natural-language/keyword search box → merged, de-duplicated results from OpenAlex
+ arXiv → scored result cards (title, authors, source badges, all component
scores, short AI relevance blurb) → `Paper` detail view (score breakdown,
Experiment Setup, repo link, conditional code-gen action).

- Bedrock expands the query **and** writes per-result relevance; ranking is a
  **non-AI blend**: `Final Score = 0.7·relevance + 0.3·reproducibility` (weight
  in config). All component scores shown; results sorted by Final Score.
- Papers cached in Postgres; scores computed **async** and attached as they
  complete (score shows `pending` first). Searches themselves not persisted.
- Introduces `Paper`.
- **Depends on:** `reproducibility-scoring` for the repro component (can stub the
  score to ship search first).
- **Blocks:** nothing hard; it is the main demo surface.
- **Spec:** `.kiro/specs/paper-search/` (requirements → design → tasks).
  Reproducibility is stubbed behind a `score_reproducibility(paper_id)` seam that
  `reproducibility-scoring` later replaces at the same signature.

### Spec 3 — `reproducibility-scoring` — **drafted**

Compute a `Reproducibility Score` for a `Paper` from: repo existence +
repo-quality heuristics (README / license / tests / recent activity, via the Git
host API) **plus** completeness of the LLM-extracted `Experiment Setup`
(hyperparameters, datasets, environment) from the manuscript/source. Number is
rule-based over these signals; the LLM extracts the Experiment Setup and can
explain the score, but does not invent the number.

- Introduces `ReproducibilityScore` and `ExperimentSetup`.
- Runs async (BackgroundTasks); results cached on the `Paper`.
- **Depends on:** `paper-search` for the `Paper` it scores.
- **Blocks:** meaningful ranking in `paper-search`; `code-generation` (uses the
  Experiment Setup).
- **Spec:** `.kiro/specs/reproducibility-scoring/`. First iteration is
  **GitHub-only** (behind a `RepoHost` interface) and scores Reader-side material
  only (abstract + links); Writer-uploaded material comes with `writer-workspace`.
  Replaces the `paper-search` repro stub at the same seam.
- **Cross-spec alignment with `paper-search`:** the normalized `experiment_setups`
  table is the source of truth and is **mirrored** into the existing
  `papers.experiment_setup` JSON column (`{hyperparameters, datasets,
  environment, available}`) so paper-search's detail read path is unchanged; the
  reproducibility breakdown reaches the UI via an additive, nullable
  `reproducibility_breakdown` field on `GET /api/papers/{id}`.

### Spec 4 — `code-generation` (opt-in, off by default, never executed) — **drafted**

Three cases:

1. **Reader, no repo** — generate source code from scratch grounded in the
   Experiment Setup, plus a README overview.
2. **Reader, has repo** — align/annotate the *existing* source so it matches the
   Experiment Setup and README (not generated from scratch).
3. **Writer** — generate code from the Writer's uploaded manuscript + source.

Display and download only; we never run or verify the output.

- Introduces `GeneratedCode` (`Generation` + `GenerationJob`).
- **Depends on:** `reproducibility-scoring` (Experiment Setup) and
  `paper-search` (Reader cases); case 3 depends on `writer-workspace`.
- **Spec:** `.kiro/specs/code-generation/`. Consumes the `Experiment Setup` and
  Paper-level `Reproducibility Score` as existing inputs (does not extract or
  compute them); the Artifact Code-Quality Score never feeds a Paper's repro
  score (ADR-0004).

### Spec 5 — `writer-workspace` — **drafted**

Writer claims a paper and uploads material to evaluate/generate against:

- Claim a paper by link/DOI/arXiv-id and/or upload.
- **Uploads:** PDF manuscript (server-side text extraction) + source as
  **zip/tarball or public Git URL**. Writer-owned manuscript text and source
  **are persisted** (ADR-0003), in Postgres.
- Reuses `reproducibility-scoring` and `code-generation` (case 3) over the
  Writer's own paper; **produces** the persisted uploads those features consume.
- Introduces `PaperClaim`, `WriterManuscript`, `WriterSourceFile`.
- **Depends on:** `accounts` (`User` ownership), `reproducibility-scoring`,
  `code-generation`.
- **Spec:** `.kiro/specs/writer-workspace/`. Grilled (`/grill-with-docs`); the
  settled decisions are in `GLOSSARY.md` (Paper Claim, Paper Reference, Writer
  Manuscript, Writer Source File) and two ADRs: **ADR-0005** (upload ingestion is
  synchronous, not a background job) and **ADR-0006** (a public Git URL is fetched
  as an HTTP codeload tarball, not cloned). Stored source is text-only (binaries
  skipped); claims de-dupe per identifier scheme.

### Suggested build order

`accounts` → `paper-search` (with a stubbed repro score) →
`reproducibility-scoring` (unstub ranking) → `code-generation` →
`writer-workspace`.

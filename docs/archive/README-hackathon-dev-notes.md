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
2. Clone the repo. The shared skills under `.claude/skills/` come with it — no
   per-machine install. Install the `ponytail` plugin once
   (`/plugin install ponytail@ponytail`).
3. `cp .env.example .env`
4. `docker compose up --watch` — first run builds images and applies database
   migrations automatically.
5. Start Claude Code in the repo root so it loads `CLAUDE.md`, the skills in
   `.claude/skills/`, and the Playwright MCP server from `.mcp.json`.

> The project context (product, stack, layout, workflow, verification gates) is in
> [`CLAUDE.md`](CLAUDE.md), which Claude Code loads every session.

### Developing a feature

The per-feature loop (formalized in [`CLAUDE.md`](CLAUDE.md)):

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
│   └── update-skills.sh  # compare vendored skills with pinned upstream commits
├── CLAUDE.md           # project context + workflow, loaded every session
├── .claude/
│   └── skills/         # skills, shared via git (see below)
├── .mcp.json           # Playwright MCP server
├── specs/              # per-feature requirements / design / tasks
├── TODO.md             # implementation status and follow-ups
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
scripts/demo-reset.sh    # empty DB, DEMO_MODE=replay, demo account (demo / demo-password-1)
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
[`.claude/skills/SKILLS.md`](.claude/skills/SKILLS.md) pins each to the upstream
commit it came from (that file is the "lockfile"):

```bash
./scripts/update-skills.sh      # fetch pinned upstream copies, show how ours differ
```

The script never overwrites the vendored files. To update: bump the SHA in both
`scripts/update-skills.sh` and `.claude/skills/SKILLS.md`, run the script, review
the printed diffs, and hand-apply any upstream changes worth taking.

## Frontend status (first iteration)

The React frontend (`Reader` + `Writer` UI) is implemented for **all five specs**
and merged to `main`, one spec per PR (#5–#9). Each was built with the `ponytail`
and `frontend-design` skills; frontend-only, with the backend layers still to
come.

| Spec | UI | Key components (`frontend/src/`) |
| --- | --- | --- |
| `accounts` | Auth gate, login/register, mode toggle | `components/{AuthProvider,AuthBar,LoginForm,RegisterForm,Field}.tsx`, `api/auth.ts` |
| `paper-search` | Reader search → ranked cards (live score polling) → paper detail | `components/{SearchBox,ResultList,ResultCard,ScoreBar,SourceBadges,PaperDetail}.tsx`, `components/useScorePolling.ts`, `api/papers.ts` |
| `reproducibility-scoring` | Detail-view score breakdown, Experiment Setup, explanation | `components/PaperDetail.tsx` (extended), `api/papers.ts` (extended) |
| `code-generation` | Opt-in generate action, job polling, two-pane artifact view + download, generations list | `components/{GenerateButton,JobStatusView,ArtifactView,GenerationsList}.tsx`, `api/codegen.ts` |
| `writer-workspace` | Writer-mode workspace: claim, manuscript/source upload, delete controls | `components/writer/*`, `api/writer.ts` |

**Shared design system.** A small token set lives in `frontend/src/index.css`
(`ink`, `paper`, `accent` teal, `caution` amber, `hairline`, `muted`); the UI is
one cohesive surface — an auth gate wraps a Reader search experience and a Writer
workspace, switched by the `accounts` mode toggle. Amber `caution` is reserved
for destructive confirmations and failure/unverified states (never decoration).

**How it's wired.** Every API client uses `credentials: "include"` (the session
cookie) and per-request `AbortController` timeouts. The app is a single
`App.tsx` view-state machine (no router dependency).

**Verification caveat.** The frontend is verified by type-check only
(`pnpm lint` → `tsc --noEmit`), the project's only frontend gate — there is no
automated frontend test suite (the team tests the UI manually). The UIs call
`/api/*` endpoints that **do not exist until each spec's backend lands**, so the
end-to-end manual walkthroughs (each spec's final checkpoint) are still pending.
Two deliberate deviations from the design docs: the `code-generation` and
`writer-workspace` docs name IBM Plex fonts, but the implementation uses the CSS
`monospace` generic to avoid a web-font dependency; and client-side upload size
gates hardcode the backend's default limits (keep them in sync if those
`Settings` change).

## Business logic status (first iteration)

The framework-agnostic business-logic layer (`backend/app/services/` and
`core/security.py`) is implemented and verified by its offline test gate (pytest
+ Hypothesis; external Sources and the LLM are mocked, never called for real).

| Spec | Business logic (`backend/app/`) | Verified by |
| --- | --- | --- |
| `accounts` | `core/security.py` — Argon2 hashing, verification, credential-format validation | `tests/test_security_properties.py` (6 passed) |
| `paper-search` | `services/{ranking,merge,reproducibility}.py`, `services/sources/*`, `services/llm.py` | `tests/{test_ranking_properties,test_merge_properties,test_sources}.py` (13 passed) |
| `reproducibility-scoring` | `services/repro/*` — rule-based scorers (`code_quality`, `completeness`, `scorer`), GitHub `inspector`, LLM `extractor`/`explainer` | `tests/{test_repro_scorers_properties,test_repro_inspector}.py` (17 passed) |
| `code-generation` | `core/codegen.py` — `Generation_Helper` (`generate`, README-always/Python-default) + `Scoring_Helper` (`score`), Bedrock via LangChain | `tests/test_codegen_helper_properties.py` (7 passed) |
| `writer-workspace` | `core/extraction.py` — `Extraction_Helper`: `extract_pdf_text` (pypdf), `unpack_archive` (zip/tar, text-only, path-safe, capped) | `tests/test_extraction_properties.py` (8 passed) |

Run the gate on the host: `cd backend && uv run pytest`. The ranking/merge/source
tests need no Docker; the full suite (API + migrations) needs a reachable Docker
daemon for testcontainers.

> **Scoring-model update (pending).** `reproducibility-scoring` is being realigned
> to the **Standards-Conformance Score** in [`scoring_rule.md`](scoring_rule.md)
> v1.2 — the weighted Q/D model with the TRIPOD+AI (Medicine) and merged
> ACM/ML/FAIR4RS (CS) standards. The spec, ADR-0008/0009, and the
> `ReproducibilityScore` model are updated; the `standards/` adapter rewrite and
> its migration are re-opened tasks (see `specs/reproducibility-scoring/tasks.md`,
> §Redesign). The currently passing scorer tests cover the earlier blend.

## Planned specs

The product was grilled (`/grill-with-docs`) into shared understanding before any
spec was written. See `GLOSSARY.md` and `docs/adr/0001..0006` for the settled
vocabulary and decisions. The work is split into focused specs rather than one
mega-spec; build them in dependency order.

**All five specs are drafted** (requirements → design → tasks, under
`specs/`): `accounts`, `paper-search`, `reproducibility-scoring`,
`code-generation`, and `writer-workspace`. The **frontend layer of all five is
implemented and merged** for this first iteration (see
[Frontend status](#frontend-status-first-iteration) below); the backend and
business-logic layers are still pending. The specs were drafted out of dependency
order, so each stands on documented assumptions about its not-yet-implemented
inputs (noted per spec); implement the remaining layers in the build order.

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

> **Status key:** each spec below is **drafted** (spec written) and **frontend
> done** (UI implemented + merged); backend and business-logic layers are pending.

### Spec 1 — `accounts` (foundation) — **frontend done**

Lightweight auth: username + password registration/login, session handling. One
account; both Reader and Writer modes available to it. Introduces the `User`
table.

- **Depends on:** nothing.
- **Blocks:** `writer-workspace` (needs `User` to own a `PaperClaim`).

### Spec 2 — `paper-search` (Reader entry point) — **frontend done**

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
- **Spec:** `specs/paper-search/` (requirements → design → tasks).
  Reproducibility is stubbed behind a `score_reproducibility(paper_id)` seam that
  `reproducibility-scoring` later replaces at the same signature.

### Spec 3 — `reproducibility-scoring` — **frontend done**

Compute a `Reproducibility Score` for a `Paper` by evaluating it against a
published standard selected by its **field of study**, following the
**Standards-Conformance Score** defined in [`scoring_rule.md`](scoring_rule.md)
(v1.2). The number is rule-based; the LLM extracts the `Experiment Setup` and
supplies per-criterion evidence, and can explain the score, but never invents the
number.

- **Two fields, different standards:** Medicine → **TRIPOD+AI** (26 weighted
  criteria); Computer Science → a merged **ACM Artifact Review & Badging v1.1 +
  ML Code Completeness Checklist + FAIR4RS v1.0** standard (25 weighted criteria);
  `unknown` → a domain-neutral **baseline**. The field of study is captured at
  ingestion from the source classifier (OpenAlex field id, arXiv category) and
  persisted on the `Paper`.
- **Weighted Q/D roll-up:** each criterion carries a classification tag — **Q**
  (code/tool quality) or **D** (paper-to-code discrepancy; `Q/D` counts in D) — a
  weight, a display category, and its source reference(s). Within each field the Q
  weights sum to `0.30` and the D + Q/D weights sum to `0.70`, so the score is
  `S = 0.30·S_Q + 0.70·S_D`. Each criterion scores met=1 / partial=0.5 / unmet=0 /
  NA, confidence-adjusted; NA criteria are dropped and weights renormalized within
  their group. Repo-quality signals (README / license / tests / recent activity,
  via the Git host API) and `Experiment Setup` completeness feed the criteria.
- Introduces `ReproducibilityScore` (which records the field of study, selected
  standard, `S_Q`/`S_D`, and the full per-criterion result) and `ExperimentSetup`.
- Runs async (BackgroundTasks); results cached on the `Paper`.
- **Depends on:** `paper-search` for the `Paper` it scores.
- **Blocks:** meaningful ranking in `paper-search`; `code-generation` (uses the
  Experiment Setup and the per-criterion `Standard Result`).
- **Spec:** `specs/reproducibility-scoring/`. First iteration is
  **GitHub-only** (behind a `RepoHost` interface) and scores Reader-side material
  only (abstract + links); Writer-uploaded material comes with `writer-workspace`.
  Replaces the `paper-search` repro stub at the same seam. The scoring model lives
  behind a `select_standard(field_of_study)` adapter (ADR-0008); the roll-up is
  deterministic and never produced by the LLM (ADR-0009).
- **Cross-spec alignment with `paper-search`:** the normalized `experiment_setups`
  table is the source of truth and is **mirrored** into the existing
  `papers.experiment_setup` JSON column (`{hyperparameters, datasets,
  environment, available}`) so paper-search's detail read path is unchanged; the
  reproducibility breakdown reaches the UI via an additive, nullable
  `reproducibility_breakdown` field on `GET /api/papers/{id}`.

### Spec 4 — `code-generation` (opt-in, off by default, never executed) — **frontend done**

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
- **Spec:** `specs/code-generation/`. Consumes the `Experiment Setup` and
  Paper-level `Reproducibility Score` as existing inputs (does not extract or
  compute them); the Artifact Code-Quality Score never feeds a Paper's repro
  score (ADR-0004).

### Spec 5 — `writer-workspace` — **frontend done**

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
- **Spec:** `specs/writer-workspace/`. Grilled (`/grill-with-docs`); the
  settled decisions are in `GLOSSARY.md` (Paper Claim, Paper Reference, Writer
  Manuscript, Writer Source File) and two ADRs: **ADR-0005** (upload ingestion is
  synchronous, not a background job) and **ADR-0006** (a public Git URL is fetched
  as an HTTP codeload tarball, not cloned). Stored source is text-only (binaries
  skipped); claims de-dupe per identifier scheme.

### Suggested build order

`accounts` → `paper-search` (with a stubbed repro score) →
`reproducibility-scoring` (unstub ranking) → `code-generation` →
`writer-workspace`.

---
name: spec
description: >
  Spec-driven development for Kaelo features. `/spec new <feature>` drafts
  requirements.md, design.md, tasks.md under specs/<feature>/ with an approval
  gate between each; `/spec run <feature> [task-id]` implements tasks and ticks
  them off; `/spec status [feature]` shows progress. Use for feature work (changes
  a functional requirement/user story or is a breaking change), not for typos or
  one-file fixes.
argument-hint: new <feature> | run <feature> [task-id] | status [feature]
---

# Spec workflow

Requirements-first. Each feature lives in `specs/<feature>/` as three markdown
files that already exist for the five shipped features (`accounts`,
`paper-search`, `reproducibility-scoring`, `code-generation`,
`writer-workspace`). **Read one of them (e.g. `specs/writer-workspace/`) before
drafting a new spec and match its depth and structure.** Parse `$ARGUMENTS` as
`<subcommand> <feature> [task-id]`; `<feature>` is a kebab-case folder name. If
the subcommand is missing or unknown, show the usage in `argument-hint`.

Ground rules: use the terms in `GLOSSARY.md`; respect `docs/adr/`; don't invent
requirements, ask. A spec that was grilled with `/grill-with-docs` should carry
those decisions, not re-ask them.

## `/spec new <feature>`

Stop and get the user's approval after **each** file before writing the next.

1. **Prepare.** If `specs/<feature>/` exists, stop and ask whether to continue
   or revise. Read `CLAUDE.md`, `GLOSSARY.md`, the ADR list, and any existing
   code the feature touches. If the request is still fuzzy, suggest
   `/grill-with-docs` first.
2. **`requirements.md`**: sections, in order:
   - `# Requirements Document`, `## Introduction` (what, why, what it consumes,
     which ADRs apply, and an explicit **Out of scope** paragraph).
   - `## Glossary`: `**Term_Name**: definition` for every named component or
     concept the criteria use (e.g. `Auth_UI`, `Auth_API`, `Credential_Helper`).
   - `## Requirements`: `### Requirement N: <Title> (<Layer>)` where layer is
     Frontend / Backend / Business Logic, as the project's layering convention.
     Each has a `**User Story:** As a …, I want …, so that …` and numbered
     `#### Acceptance Criteria` in **EARS** form: `WHEN … THE <Component> SHALL
     …`, `WHILE …`, `IF … THEN THE <Component> SHALL …`, `THE <Component> SHALL
     …`. Criteria must be concrete and testable (limits, timeouts, status
     codes, what is retained or cleared), never "should be fast".
3. **`design.md`**: `# Design Document`; `## Overview` (layer/component/requirements
   table + **Key design decisions** with trade-offs; flag candidates for an ADR);
   `## Architecture` (diagram and flows, each tagged with the requirements it
   serves); `## Components and Interfaces` (one subsection per layer, headed with
   its requirement IDs); `## Data Models` (tables, Alembic migration, config
   settings); `## Correctness Properties` (numbered `### Property N: <statement>`,
   each "for any …" universal and tagged with requirements validated; these drive
   property tests); `## API Endpoint Contracts`; `## Error Handling`;
   `## Security`; `## Testing Strategy` (property tests via Hypothesis, ≥100
   iterations, tagged `# Feature: <name>, Property N: …`; example/edge tests via
   pytest; integration/smoke; **no frontend test suite**, manual only). For UI
   work, apply `/frontend-design` and include a design-direction section.
4. **`tasks.md`**: `# Implementation Plan: <feature>`; `## Overview` and a bullet
   list of gates (below); `## Tasks` as nested checkboxes:
   - Top-level `- [ ] N. <Layer> — <component>`; sub-tasks `- [ ] N.M <action>`
     with a concrete description (file paths, signatures, `uv add …`) and
     `_Requirements: X.Y, …_` traceability. Every requirement is covered by at
     least one task.
   - Mark optional tasks (mainly tests) `- [ ]*`. Every property in the design
     gets a `Write property test — <statement>` sub-task.
   - Order bottom-up: business logic, then backend (model, migration, router,
     registration in `main.py`), then frontend. After each layer add a
     `Checkpoint` task ("run the gate, ask the user if anything is unclear").
     End with a final checkpoint (manual browser verification for UI).
   - Finish with a `## Task Dependency Graph` fenced `json` block:
     `{"waves": [{"id": 0, "tasks": ["1.1", "3.1"]}, …]}`; tasks in one wave
     don't depend on each other, and later waves depend on earlier ones.

   Standing gates to restate in the overview: backend `cd backend && uv run
   pytest` after every backend task; Alembic migration committed, never
   `create_all`; all LLM calls mocked in tests; `uv`/`pnpm` only; no frontend
   test gate.

## `/spec run <feature> [task-id]`

1. Read all three spec files, `CLAUDE.md`, and the ADRs they cite. Stop if any
   spec file is missing.
2. Pick the work: the given `task-id` (a parent runs its sub-tasks in order), or
   the first unchecked **required** task whose wave dependencies are done. Skip
   `*` optional tasks unless the user names them or says to include them.
3. Implement with the `ponytail` skill: smallest change that fully satisfies the
   task's `_Requirements_`. Follow existing code conventions; don't touch
   unrelated code. If the task conflicts with the code or an ADR, stop and
   surface it; don't silently deviate. Deliberate deviations are recorded in the
   spec afterward.
4. Verify per the task: run the backend gate for backend work (`cd backend &&
   uv run pytest`), `pnpm lint` for frontend, and for property tests confirm they
   fail when the property is broken. A frontend task is verified manually; say
   what was and wasn't checked in a browser.
5. Tick the checkbox(es) in `tasks.md` only when verified. A failing gate leaves
   the task unchecked. At a `Checkpoint` task, run the gate and report; don't tick
   it if anything fails or the user hasn't confirmed manual verification.
6. Run one top-level task per invocation unless told otherwise, then summarize:
   files changed, gate results, what's next. Don't commit unless asked.

## `/spec status [feature]`

Count `- [x]` vs `- [ ]` (and `- [ ]*` optional) per `tasks.md`; for each feature
print done/open/optional-open and the next runnable task. With no feature, cover
all of `specs/*`. Read-only.

## After a feature ships

Apply the litmus test from `CLAUDE.md`: anything still true project-wide goes to
`CLAUDE.md` or an ADR, not left buried in the spec.

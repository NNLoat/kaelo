# Open Science Paper Engine

An AI-assisted search engine for scientific papers that advances open science:
it finds papers, scores their reproducibility, and helps close the gap when a
paper ships without usable code. Scope is scientific papers in the **Computer
Science** and **Medicine** domains.

## Language

**Paper**:
A scientific publication indexed from an external source. We store only its
index metadata and links, never its full text.
_Avoid_: Article, document, work

**Index**:
The metadata and links we persist for a Paper (title, authors, abstract, DOI,
source links, repository link if any). The thing we store instead of full text.

**User**:
An authenticated account (username + password). Every User can use both Reader
and Writer features; the two are modes, not separate account types.

**Reader**:
A mode in which a User finds, reads, and evaluates papers written by others.
_Avoid_: Reviewer

**Writer**:
A mode in which a User evaluates the reproducibility of a paper they claim as
their own.
_Avoid_: Author (reserve "author" for the person credited on a Paper, who is
not necessarily a User of our system)

**Reproducibility Score**:
A rating of how reproducible a Paper is, derived from signals such as whether a
code repository exists, its code quality, and the completeness of the extracted
Experiment Setup. Factors into search ranking.
_Avoid_: Repro score, rating

**Final Score**:
The blended ranking score for a search result: a weighted combination of text
relevance and the Reproducibility Score (default 0.7 relevance / 0.3 repro,
weight in config). Results are sorted by Final Score, and all component scores
are shown to the user.

**Experiment Setup**:
The structured, machine-readable description of how to reproduce a Paper's
results (e.g. hyperparameters, datasets, environment), extracted by the LLM from
the manuscript and/or source code. We store this derived artifact, not the
source full text.
_Avoid_: Config, parameters

**Code-Quality Score**:
A rating of code quality. Two distinct subjects share the name and must not be
conflated:
- **Repository Code-Quality Score** — rates a Paper's associated *existing* code
  repository. An input to the Reproducibility Score.
- **Artifact Code-Quality Score** — rates the *generated/aligned* code a
  Generation produces. It lives on the Generation only and never feeds back into
  any Paper's Reproducibility Score, because generated code is unverified and
  unexecuted. See `docs/adr/0004-generated-code-never-feeds-paper-repro-score.md`.

**Generation**:
A persisted, derived artifact a Code Generation action produces for one User: a
set of generated files (code plus a README) with an Artifact Code-Quality Score
and an "unverified, not executed" disclaimer. A Generation references a Paper by
its index identifier and never stores external full text or external repository
contents. Owned by and visible only to the User who created it. A re-run produces
a new Generation that supersedes the prior one as "latest"; superseded
Generations are retained until the owning User deletes them.

**Generation Job**:
The unit of work that produces a Generation. Started on explicit, per-action
opt-in by a User, it runs asynchronously and ends in exactly one terminal state:
**succeeded** (a Generation was produced), **failed** (a backend/LLM error, no
artifact), or **refused** (a precondition was missing — e.g. no Experiment Setup,
Align requested on a Paper with no repository, or Writer generation with nothing
uploaded). At most one in-flight Job exists per (User, Paper, case); a duplicate
request returns the in-flight Job.

**Code Generation**:
Producing candidate code for a Paper, opt-in and off by default. We never
execute or verify generated code. Three cases:
- **Generate** (Reader, no repo): produce source code from scratch grounded in
  the Experiment Setup, plus a README overview.
- **Align** (Reader, has repo): refine/annotate the *existing* source so it
  matches the Experiment Setup and README — not generated from scratch.
- **Writer generation** (Writer): generate code from the Writer's uploaded
  manuscript and uploaded source code.
_Avoid_: Codegen, synthesis

**Upload**:
A manuscript (PDF, via server-side text extraction) and/or source code (zip or
tarball, or a public Git URL) a Writer provides for a paper they claim.
Uploaded manuscript text and source code **are persisted for Writers** (the User
owns the work). This is the deliberate exception to the index-only rule, which
still holds for Reader-side indexed Papers. Ingestion is synchronous
(`docs/adr/0005`); a Git URL is fetched as an HTTP archive, not cloned
(`docs/adr/0006`).
_Avoid_: Attachment

## Writer workspace

**Paper Claim**:
A User's self-asserted claim to a specific paper, created from a Paper Reference
(a link, DOI, or arXiv id) and owning that paper's uploaded Writer Manuscript and
Writer Source Files. Owned by and visible only to its creating User. A claim may
exist with no uploads yet. At most one Claim exists per (User, normalized Paper
Reference); the same paper reached via two different identifier schemes is, for
now, two Claims (cross-identifier resolution is deferred to paper search).
_Avoid_: Ownership, authorship record

**Paper Reference**:
The identifier a Writer supplies to create a Paper Claim — a link, DOI, or arXiv
id — normalized to a canonical per-scheme form for de-duplication within a User's
Claims.

**Writer Manuscript**:
The persisted plain text extracted from a Writer's uploaded PDF manuscript for a
Paper Claim, with its original filename. At most one per Claim; re-uploading
replaces it. The raw PDF bytes are not retained after extraction.

**Writer Source File**:
One persisted file of a Writer's uploaded source for a Paper Claim, stored as a
(relative path, content) pair. Only decodable **text** files are kept; binary
files in an upload are skipped. The raw archive and any fetched repository
working copy are not retained after unpacking.

**Source**:
An external index we pull Papers from. Currently OpenAlex and arXiv.
_Avoid_: Provider, database

**Cassette**:
The committed JSON file (`demo/fixtures/cassette.json`) holding recorded Source,
LLM and GitHub-inspection results, so a demo in `DEMO_MODE=replay` returns
identical results with no network or AWS access. Written only by
`scripts/demo-record.sh`. See
`docs/adr/0010-demo-mode-records-and-replays-at-the-seams.md`.
_Avoid_: Fixture, snapshot, cache

## Reproducibility standards

**Domain**:
The academic field a Paper belongs to, used to select which Reproducibility
Standard applies: `computer_science`, `medicine`, or `unknown`. Captured at
ingestion from the source's own field classifier (OpenAlex field id, arXiv
category), not inferred later. See
`docs/adr/0007-domain-captured-at-ingestion-from-source-classifiers.md`.
_Avoid_: Field, subject, discipline, category

**Reproducibility Standard**:
A published set of reproducibility criteria a Paper is evaluated against,
selected by its Domain: the **ML Reproducibility Checklist** (Computer Science),
**FAIR** (Medicine), or a domain-neutral **baseline** (unknown). Each is one
implementation of a single adapter interface, so a standard can be added or
swapped without touching the scorer or the Review Report. See
`docs/adr/0008-reproducibility-standard-adapter.md`.
_Avoid_: Rubric, guideline, checklist (reserve "checklist" for the ML one)

**Criterion**:
One item of a Reproducibility Standard (e.g. "training details are reported",
"dataset is findable and accessible"). Evaluating a Paper against a standard
yields a status per Criterion.

**Criterion Status**:
The outcome of evaluating one Criterion for a Paper: **met**, **partial**,
**unmet**, or **not-applicable**, with a short evidence note. The LLM may supply
these as data; it never produces the score number. See
`docs/adr/0009-llm-supplies-evidence-score-rollup-is-deterministic.md`.

**Standard Result**:
The structured output of evaluating a Paper against a Reproducibility Standard:
the per-Criterion statuses and notes plus a deterministic `[0,1]` roll-up. The
shared artifact both features consume — the Reproducibility Score reads the
number; the Review Report reads the per-Criterion detail.

**Review Report**:
A Markdown report that reviews a Paper's manuscript and existing code against the
applicable Reproducibility Standard, identifying gaps and recommending specific
improvements. A cheaper alternative to full Code Generation that reuses the same
standard evaluation; it produces findings, not runnable code.
_Avoid_: Audit, assessment

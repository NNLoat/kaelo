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
A rating of the quality of a Paper's associated code repository. An input to the
Reproducibility Score.

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
still holds for Reader-side indexed Papers.
_Avoid_: Attachment

**Source**:
An external index we pull Papers from. Currently OpenAlex and arXiv.
_Avoid_: Provider, database

**Score Signal**:
One independent input to the Reproducibility Score — currently *repo existence*,
*repo quality* (README / license / tests / recent activity, from the Git host
API), and *Experiment Setup completeness*. Each signal carries its own value and
an availability status (`ok` / `unavailable`) so a flaky external call never
blocks the whole score.

**Repo-Quality Signal**:
The Score Signal derived from a Paper's code repository via the Git host API:
presence of a README, a license, tests, and recent commit activity. GitHub is
the only host inspected for host-specific heuristics; other hosts contribute only
the "repo exists" part of the signal.

**Setup-Completeness Signal**:
The Score Signal measuring how complete the extracted Experiment Setup is,
scored as the fraction of a fixed checklist the LLM could extract
(hyperparameters, datasets, environment/dependencies, hardware, training/eval
procedure).

**Partial Score**:
A Reproducibility Score computed from only the Score Signals that were available,
when one or more signals could not be gathered. The breakdown records which
signals were skipped and the explanation says so; the score is never failed
outright for a single unavailable signal.

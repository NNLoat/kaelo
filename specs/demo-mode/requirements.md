# Requirements Document

## Introduction

The `demo-mode` feature makes the Kaelo prototype **repeatable for a scripted live
demonstration**. Today a search is not repeatable: the sources (OpenAlex, arXiv)
are queried live, the LLM rewrites the query, rates each paper's relevance and
extracts its Experiment Setup, and the GitHub API is read for repository signals.
Any of these can change between runs. Worse, `POST /api/papers/search` returns
its cards **before** background scoring finishes and orders them by whatever
Final Score is already stored (stale from an earlier search, or none), and the
frontend sorts once on arrival and never re-sorts as scores land. The order the
audience sees therefore depends on earlier runs, not on the scores that appear.

This spec adds a `DEMO_MODE` setting with three values:

- **`off`** (default): behavior is unchanged.
- **`record`**: each call that crosses a boundary to the outside world is made
  live and its result is stored in a **Cassette** file committed to the repo.
- **`replay`**: those calls are answered from the Cassette, with no network, no
  Bedrock and no AWS credentials. A call the Cassette does not contain **falls
  back to the live call** (and is logged), so an off-script query still works.

The real pipeline (merge, scoring, the deterministic roll-up, ranking) runs
unchanged on top of the recorded values, so the demo shows real output rather than
canned cards. In `record` and `replay` modes the Search_API also **scores every
returned paper before it responds**, so the first response is fully scored and
sorted by Final Score, the same order the frontend's *Final score* sort produces.

It also adds the tooling to make a demo repeatable: a reset-and-seed script that
returns the database to a known state, a record script that runs the scripted
queries, and a short demo script document.

This spec **consumes** the existing seams without changing their contracts: the
source adapters (`docs/adr/0001`), the Bedrock/LangChain calls in query
expansion, relevance assessment, setup extraction and score explanation
(`docs/adr/0002`), the GitHub `RepoHost` inspector, and the deterministic score
roll-up (`docs/adr/0009`, which this spec does not touch). Cassette contents are
index metadata and model output only, consistent with the index-only rule
(`docs/adr/0001`). The work follows the project's layering: Backend (settings,
orchestration) and Business Logic (the Cassette and the seam wrappers).

**Assumptions** (settled with the user): the frontend is unchanged and its default
sort stays as it is; switching it to *Final score* must give the same order as the
backend response. A Cassette miss in `replay` falls back to live rather than
failing. Code generation is not recorded; it follows the existing `CODEGEN_MOCK`
setting.

Out of scope: any frontend change (including the default sort key); recording or
replaying code generation and review (use `CODEGEN_MOCK`); changing the score
formulas, weights, or the Standards-Conformance roll-up; making the live
(`off`) path deterministic; recording the Writer-workspace upload flow; a UI to
manage Cassettes; and encrypting or redacting Cassette content beyond excluding
credentials.

## Glossary

- **Demo_Mode**: The `DEMO_MODE` setting, one of `off`, `record`, `replay`.
  Default `off`.
- **Cassette**: A single JSON file of recorded seam calls, committed under
  `demo/fixtures/` (path from `DEMO_CASSETTE_PATH`).
- **Cassette_Entry**: One recorded call: the seam name, a request key, and the
  recorded result.
- **Request_Key**: A stable digest of a seam call's canonical input (for example
  the source name, effective query and limit; the full prompt text; the
  repository URL). Identical inputs always give the same key.
- **Seam**: A boundary to the outside world that Demo_Mode wraps. There are
  three: the **Source_Seam** (OpenAlex and arXiv adapter fetches), the
  **LLM_Seam** (every Bedrock `invoke` made by query expansion, relevance
  assessment, setup extraction and score explanation), and the **Repo_Seam**
  (the GitHub repository inspection).
- **Cassette_Store**: The business-logic component that loads, looks up, and
  writes Cassette_Entries.
- **Seam_Wrapper**: The component that, for a Seam, applies Demo_Mode: passes
  through, records, or replays.
- **Replay_Miss**: A `replay` lookup whose Request_Key has no Cassette_Entry.
- **Search_API**: The existing `POST /api/papers/search` endpoint.
- **Scoring_Orchestrator**: The existing scoring job (`run_scoring_for_paper`)
  and its scheduling.
- **Final_Score**: As in `GLOSSARY.md`; the ranking blend of relevance and
  reproducibility.
- **Demo_Tooling**: The scripts under `scripts/` that reset the database, record
  the scripted queries, and the document `demo/SCRIPT.md`.

## Requirements

### Requirement 1: Demo Mode Setting (Backend)

**User Story:** As the presenter, I want one setting that turns demo recording and
replay on or off, so that I can switch the app between normal and repeatable
behavior from `.env` without code changes.

#### Acceptance Criteria

1. THE Settings SHALL expose `demo_mode` read from `DEMO_MODE`, accepting exactly `off`, `record`, and `replay`, with default `off`.
2. IF `DEMO_MODE` is set to any other value, THEN THE backend SHALL fail at startup with an error naming the setting and the accepted values.
3. WHILE Demo_Mode is `off`, THE backend SHALL behave exactly as before this feature: no Cassette is read or written, no Seam call is altered, and the Search_API still returns before background scoring completes.
4. THE Settings SHALL expose `demo_cassette_path` read from `DEMO_CASSETTE_PATH`, defaulting to `demo/fixtures/cassette.json`.
5. THE `compose.yaml` SHALL forward `DEMO_MODE` and `DEMO_CASSETTE_PATH` to the backend with defaults `off` and the container path of the bind-mounted repo `demo/` directory (`/demo/fixtures/cassette.json`), and THE `.env.example` SHALL document both with placeholders only.
6. THE backend container SHALL have the repo `demo/` directory bind-mounted read-write, so the Cassette is readable in `replay` mode and writable in `record` mode.

### Requirement 2: Cassette Storage and Request Keys (Business Logic)

**User Story:** As the presenter, I want recorded calls stored in one reviewable
file with stable keys, so that a replay reliably finds what was recorded and the
file diffs cleanly in git.

#### Acceptance Criteria

1. THE Cassette_Store SHALL read and write the Cassette as a single JSON document containing a format version and a mapping from `<seam>:<Request_Key>` to the Cassette_Entry.
2. THE Cassette_Store SHALL compute a Request_Key as a SHA-256 digest of the seam's canonical input, so that the same input always yields the same key within and across processes.
3. THE Cassette_Store SHALL serialize the Cassette with sorted keys and a fixed indentation, so that recording the same calls twice produces a byte-identical file.
4. WHEN the Cassette_Store writes the Cassette, THE Cassette_Store SHALL write to a temporary file in the same directory and rename it over the target, so that an interrupted write never leaves a truncated Cassette.
5. IF the Cassette file does not exist, THEN THE Cassette_Store SHALL treat it as empty.
6. IF the Cassette file exists but is not valid JSON or has an unsupported format version, THEN THE Cassette_Store SHALL raise an error naming the path, and SHALL NOT overwrite the file.
7. THE Cassette_Store SHALL store each Cassette_Entry's recorded result and the seam name, and SHALL NOT store credentials, tokens, request headers, or environment values.

### Requirement 3: Record Mode (Business Logic)

**User Story:** As the presenter, I want to run my scripted queries once against
the real sources and models and capture the results, so that the demo replays
genuine output.

#### Acceptance Criteria

1. WHILE Demo_Mode is `record`, WHEN a Seam call is made, THE Seam_Wrapper SHALL perform the live call and, on success, store the result in the Cassette under that call's Request_Key.
2. WHILE Demo_Mode is `record`, IF the live call raises an error, THEN THE Seam_Wrapper SHALL propagate the error unchanged and SHALL NOT store an entry, so the failure is not replayed later.
3. WHILE Demo_Mode is `record`, IF the Cassette already holds an entry for the Request_Key, THEN THE Seam_Wrapper SHALL replace it with the new result.
4. WHILE Demo_Mode is `record`, THE Seam_Wrapper SHALL return the live result to the caller exactly as it would with Demo_Mode `off`.
5. WHILE Demo_Mode is `record`, THE Cassette_Store SHALL persist the Cassette no later than the end of the request that made the calls.

### Requirement 4: Replay Mode (Business Logic)

**User Story:** As the presenter, I want the demo to run without network or AWS
access and still survive an unscripted query, so that the demo works on bad
Wi-Fi and I am not trapped by the script.

#### Acceptance Criteria

1. WHILE Demo_Mode is `replay`, WHEN a Seam call has a Cassette_Entry for its Request_Key, THE Seam_Wrapper SHALL return the recorded result and SHALL NOT make a network call, a Bedrock call, or a GitHub call.
2. WHILE Demo_Mode is `replay`, THE backend SHALL start and serve requests when `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are empty, so long as `BEDROCK_MODEL_ID` and `SESSION_SECRET` are set.
3. WHILE Demo_Mode is `replay`, WHEN a Replay_Miss occurs, THE Seam_Wrapper SHALL perform the live call and return its result, applying the existing failure handling of that call site unchanged.
4. WHEN a Replay_Miss occurs, THE Seam_Wrapper SHALL log one warning naming the seam and the Request_Key digest, and SHALL NOT log credentials or prompt text.
5. WHILE Demo_Mode is `replay`, THE Seam_Wrapper SHALL NOT write to the Cassette, including after a Replay_Miss.
6. WHILE Demo_Mode is `replay`, a recorded result SHALL be returned to the caller in the same type and shape as the live call returns (a list of source records for the Source_Seam, the model's message for the LLM_Seam, the repository signals for the Repo_Seam).

### Requirement 5: Seams Covered (Business Logic)

**User Story:** As the presenter, I want every non-repeatable input recorded, so
that nothing live can reorder the demo's results.

#### Acceptance Criteria

1. THE Source_Seam SHALL wrap each source adapter's `fetch`, keying on the adapter name, the effective query, the result limit, and the configured source domains.
2. THE LLM_Seam SHALL wrap every Bedrock `invoke` made by `expand_query`, `assess_relevance`, `extract_setup`, and `explain`, keying on the full prompt text.
3. THE Repo_Seam SHALL wrap the GitHub repository inspection, keying on the repository URL, and SHALL record the resulting repository signals.
4. THE Seam_Wrappers SHALL NOT wrap code generation, code scoring, or review; those SHALL continue to follow `CODEGEN_MOCK` regardless of Demo_Mode.
5. THE Seam_Wrappers SHALL be applied at the call sites' existing boundaries without changing the signatures of `expand_query`, `assess_relevance`, `extract_setup`, `explain`, `inspect_repo`, or the adapters' `fetch`.
6. WHERE a paper has no repository URL, THE Repo_Seam SHALL return the existing not-inspectable result without a Cassette lookup.

### Requirement 6: Deterministic, Fully Scored Search Response (Backend)

**User Story:** As the presenter, I want the first search response to carry
final scores in the right order, so that the audience sees the ranking I rehearsed
and the *Final score* sort shows the same order.

#### Acceptance Criteria

1. WHILE Demo_Mode is `record` or `replay`, WHEN the Search_API receives a valid search request, THE Search_API SHALL run the Scoring_Orchestrator for every returned paper to completion before it responds.
2. WHILE Demo_Mode is `record` or `replay`, THE Search_API SHALL respond with every score cell in a terminal state (`ready` or `unavailable`) and none `pending`.
3. WHILE Demo_Mode is `record` or `replay`, THE Search_API SHALL sort the returned cards by Final_Score descending, with `unavailable` last, using the paper's database id ascending as the tie-break.
4. WHILE Demo_Mode is `record` or `replay`, THE Search_API SHALL compute each card's scores from the values produced by this request's scoring run, never from scores stored by an earlier search.
5. WHILE Demo_Mode is `replay`, for the same query and the same Cassette, THE Search_API SHALL return the same cards in the same order with the same score values on every request.
6. THE ordering of a fully scored Search_API response SHALL equal the ordering the frontend's *Final score* sort produces for the same cards, so that no frontend change is required.
7. WHILE Demo_Mode is `off`, THE Search_API SHALL keep its existing asynchronous scoring and response ordering unchanged.

### Requirement 7: Repeatable Demo Environment (Demo Tooling)

**User Story:** As the presenter, I want to reset the app to a known state and
rehearse from a written script, so that every run of the demo starts identically.

#### Acceptance Criteria

1. THE Demo_Tooling SHALL provide `scripts/demo-reset.sh`, which stops the stack, drops the database volume, rebuilds and starts the backend with `DEMO_MODE=replay`, waits for the backend to report healthy, and registers the demo account.
2. WHEN `scripts/demo-reset.sh` completes, THE database SHALL contain no papers, scores or generations, so that paper ids are assigned from the same starting point on every run.
3. THE Demo_Tooling SHALL provide `scripts/demo-record.sh`, which starts the backend with `DEMO_MODE=record`, runs each query listed in `demo/queries.txt` through the Search_API, and exits non-zero if any query fails.
4. THE `scripts/demo-record.sh` SHALL print, for each query, the ordered titles and Final_Scores returned, so the presenter can review them before committing the Cassette.
5. THE Demo_Tooling SHALL provide `demo/SCRIPT.md`, listing the scripted queries in the order to present them, the expected top results for each, the settings the demo requires (`DEMO_MODE=replay`, `QUERY_EXPANSION_ENABLED`, `CODEGEN_MOCK=true`), and the steps to re-record.
6. THE Demo_Tooling SHALL NOT change the Cassette unless `demo-record.sh` is run.

### Requirement 8: Safety and Defaults (Backend)

**User Story:** As the maintainer, I want demo behavior to be impossible to enable
by accident and to never leak secrets, so that the normal app and the repository
stay safe.

#### Acceptance Criteria

1. THE default configuration (no `DEMO_MODE` set) SHALL be Demo_Mode `off`.
2. THE Cassette SHALL contain only source index metadata, LLM prompts and responses, and repository signals, and SHALL NOT contain `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `GITHUB_TOKEN`, `SESSION_SECRET`, or any HTTP header.
3. WHILE Demo_Mode is not `off`, THE backend SHALL log one line at startup stating the mode and the Cassette path.
4. WHEN a Seam call in `record` mode would store an entry whose serialized form contains a configured secret value (`AWS_SECRET_ACCESS_KEY`, `GITHUB_TOKEN`, or `SESSION_SECRET`), THE Cassette_Store SHALL refuse to write it and raise an error.
5. THE test suite SHALL cover Demo_Mode `off`, `record` and `replay` with all Seams mocked, and SHALL NOT call a live source, Bedrock, or GitHub.

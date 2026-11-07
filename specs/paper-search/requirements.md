# Requirements Document

## Introduction

The `paper-search` feature is the Reader entry point and the main demo surface of
the Open Science Paper Engine. A `User` in `Reader` mode enters a
natural-language or keyword query; the system expands the query with the LLM,
fetches candidate papers from the two configured `Source`s (OpenAlex + arXiv,
scoped to Computer Science and Medicine), merges and de-duplicates them into a
unified `Paper`, scores each result, and presents ranked result cards that lead
to a `Paper` detail view. This spec introduces the `Paper` table and the
Reader-facing search and detail surfaces.

Ranking is a deliberate split between AI and non-AI work. The LLM does two
things: it **expands the query** before fetching, and it **writes a per-result
relevance assessment** (a numeric relevance score plus a short natural-language
blurb). The ranking itself is a **non-AI blend**:
`Final Score = 0.7 · relevance + 0.3 · reproducibility` (weights in config). All
component scores are shown to the `User`, and results are sorted by `Final
Score`.

Scoring is asynchronous. A search returns quickly with the merged `Paper` set and
whatever scores are already available; component scores that are still being
computed show as `pending` and are attached to the cached `Paper` as they
complete. `Paper`s are **cached in Postgres** (index metadata and links only, per
the index-only rule); the **searches themselves are not persisted**.

Per the build order, this spec depends on `reproducibility-scoring` for the
reproducibility component but **must be able to ship first with that component
stubbed** — the ranking blend and all score plumbing work against a stubbed
reproducibility value until the real scorer lands.

The work is layered into three concerns, matching the convention set by the
`accounts` spec — Frontend (React `Reader` UI), Backend (FastAPI search/detail
endpoints, `Paper` persistence/caching, async scoring orchestration), and
Business Logic (source fetch/merge/de-duplication, LLM query expansion and
relevance assessment via Bedrock/LangChain, and the non-AI `Final Score` blend).

Scope is limited to Reader-side search and the `Paper` detail view. Account
registration/login (the `accounts` spec), the real reproducibility computation
(`reproducibility-scoring`), code generation (`code-generation`), and Writer
uploads (`writer-workspace`) are out of scope here. Where this spec references a
reproducibility value or a code-generation action, it specifies only the
Reader-facing surface and the stub/seam, not those features' internals.

## Glossary

- **Search_System**: The paper-search subsystem introduced by this spec,
  spanning the frontend `Reader` UI, the backend search and detail endpoints, the
  `Paper` cache, the async scoring orchestration, and the business-logic helpers
  (source fetch/merge, LLM assist, score blend).
- **Search_API**: The backend (FastAPI) layer that exposes the search and
  `Paper` detail endpoints, persists and reads the `Paper` cache, and orchestrates
  asynchronous scoring.
- **Search_UI**: The frontend (React) layer that renders the search box, the
  ranked result cards (title, authors, `Source` badges, all component scores, AI
  relevance blurb), the loading/pending states, and the `Paper` detail view.
- **Source**: An external index the `Search_System` pulls `Paper`s from.
  Currently OpenAlex and arXiv, scoped to Computer Science and Medicine
  (ADR-0001). The one `Paper` returned to the `User` may be backed by more than
  one `Source`.
- **Source_Adapter**: The business-logic component for one `Source` that issues
  the query against that external index and maps its native records into the
  common pre-merge paper shape. One `Source_Adapter` per `Source`.
- **Paper**: A scientific publication indexed from one or more `Source`s and
  cached in Postgres. We store only index metadata and links (title, authors,
  abstract, publication date, DOI, source links, repository link if any), never
  full text. The unit shown in results and on the detail view.
- **Merge_Dedup**: The business-logic step that combines candidate records from
  all `Source_Adapter`s into unified `Paper`s, collapsing records that refer to
  the same publication into a single `Paper` that records every contributing
  `Source`.
- **Query_Assist**: The LLM (Amazon Bedrock via LangChain) step that expands the
  `User`'s raw query into an enriched query used to fetch from the `Source`s
  (ADR-0002). AI work performed before fetching.
- **Relevance_Assessment**: The LLM (Bedrock via LangChain) output for one
  `Paper` relative to the query: a numeric `Relevance Score` and a short
  natural-language relevance blurb. AI work performed per result.
- **Relevance Score**: The numeric component, in the range 0 to 1, produced by
  the `Relevance_Assessment` for a `Paper` relative to the query. An input to the
  `Final Score`.
- **Reproducibility Score**: The numeric component, in the range 0 to 1,
  rating how reproducible a `Paper` is. Produced by the `reproducibility-scoring`
  feature; consumed here as an input to the `Final Score`. In this spec it may be
  supplied by a **stub** until that feature lands.
- **Final Score**: The non-AI blended ranking score for a result:
  `0.7 · Relevance Score + 0.3 · Reproducibility Score` (weights in config).
  Results are sorted by `Final Score`; all component scores are shown.
- **Score_Status**: The state of a component score for a cached `Paper` in the
  context of a search: `pending` while it is still being computed, `ready` once a
  value is attached, or `unavailable` if it could not be computed.
- **Reader**: A mode in which a `User` finds, reads, and evaluates papers written
  by others. The mode in which `paper-search` is used.

## Requirements

### Requirement 1: Search Entry and Submission (Frontend)

**User Story:** As a Reader, I want a search box in the web UI, so that I can
enter a natural-language or keyword query and get back relevant papers.

#### Acceptance Criteria

1. WHEN a Reader opens the search view, THE Search_UI SHALL display a search input and a submit control, with the submit control disabled while the input is empty or contains only whitespace.
2. WHEN a Reader submits a non-empty query of up to 512 characters, THE Search_UI SHALL send a search request to the Search_API carrying the submitted query text.
3. WHILE a search request is in progress, THE Search_UI SHALL display a loading indicator and disable the submit control until a response is received or the 30-second request timeout elapses.
4. WHEN the Search_API returns a result set, THE Search_UI SHALL render the returned Papers as ranked result cards in the order the Search_API returned them.
5. WHEN the Search_API returns an empty result set for a query, THE Search_UI SHALL display a message stating that no papers were found and keep the search input available for a new query.
6. IF no response is received from the Search_API within the 30-second request timeout or the request fails due to a network or server error, THEN THE Search_UI SHALL display an error message indicating that the search could not be completed and re-enable the submit control, retaining the submitted query text.
7. IF a Reader submits a new search while a previous search request is still in progress, THEN THE Search_UI SHALL abandon the earlier request and render results only for the most recently submitted query.

### Requirement 2: Result Cards (Frontend)

**User Story:** As a Reader, I want each result shown as a card with its scores
and a relevance blurb, so that I can judge a paper at a glance before opening it.

#### Acceptance Criteria

1. WHEN the Search_UI renders a result card for a Paper, THE Search_UI SHALL display the Paper title, its authors, and a Source badge for every Source that contributed to that Paper.
2. WHEN the Search_UI renders a result card, THE Search_UI SHALL display the Relevance Score, the Reproducibility Score, and the Final Score as distinct, labeled component scores.
3. WHEN a component score for a Paper has Score_Status `pending`, THE Search_UI SHALL display that score as pending rather than showing a numeric value, and SHALL display the Final Score as pending while any contributing component score is pending.
4. WHEN a component score for a Paper has Score_Status `unavailable`, THE Search_UI SHALL display that score as unavailable rather than showing a numeric value.
5. WHEN the Relevance_Assessment blurb for a Paper is available, THE Search_UI SHALL display the short relevance blurb on the result card.
6. WHEN a Reader activates a result card, THE Search_UI SHALL navigate to the Paper detail view for that Paper.
7. WHILE one or more component scores on rendered cards have Score_Status `pending`, THE Search_UI SHALL retrieve updated scores from the Search_API and replace each pending score with its value or unavailable state as it becomes available, without the Reader resubmitting the search.

### Requirement 3: Paper Detail View (Frontend)

**User Story:** As a Reader, I want a detail view for a paper, so that I can see
its full score breakdown, its experiment setup, its repository link, and the
code-generation action.

#### Acceptance Criteria

1. WHEN a Reader opens the Paper detail view for a Paper, THE Search_UI SHALL request that Paper from the Search_API by its identifier and display the Paper title, authors, abstract, publication date, every Source badge, and the external source links.
2. WHEN the Search_UI renders the Paper detail view, THE Search_UI SHALL display the score breakdown showing the Relevance Score, the Reproducibility Score, and the Final Score, each with its Score_Status.
3. IF the Paper has an associated repository link, THEN THE Search_UI SHALL display the repository link as an outbound link; OTHERWISE THE Search_UI SHALL indicate that no repository is associated with the Paper.
4. WHEN the Search_UI renders the Paper detail view, THE Search_UI SHALL display the Experiment Setup section populated from the Search_API when available and marked as not yet available otherwise.
5. WHEN the Search_UI renders the Paper detail view, THE Search_UI SHALL present a code-generation action whose availability depends on whether the Paper has an associated repository, where the action is opt-in and off by default; the action's behavior is defined by the `code-generation` feature and is out of scope for this spec.
6. IF the Search_API reports that no Paper exists for the requested identifier, THEN THE Search_UI SHALL display a not-found message and offer a way back to the search view.
7. IF the request for the Paper detail fails or times out after 30 seconds, THEN THE Search_UI SHALL display an error message and offer a retry.

### Requirement 4: Search Endpoint and Orchestration (Backend)

**User Story:** As the frontend application, I want a search endpoint, so that a
submitted query returns merged, de-duplicated, ranked Papers.

#### Acceptance Criteria

1. WHEN the Search_API receives a search request with a non-empty query of up to 512 characters, THE Search_API SHALL obtain an expanded query from Query_Assist, fetch candidate records from every configured Source via its Source_Adapter, and combine them through Merge_Dedup into a set of unified Papers.
2. WHEN the Search_API produces the Papers for a search, THE Search_API SHALL cache each Paper in Postgres and SHALL NOT persist the query text or the search request itself.
3. WHEN the Search_API returns a search response, THE Search_API SHALL include, for each Paper, its identifier, title, authors, contributing Sources, the Relevance Score, Reproducibility Score, and Final Score each with its Score_Status, and the relevance blurb when available, sorted in descending order of Final Score.
4. WHEN the Final Score for a Paper cannot yet be computed because a contributing component score has Score_Status `pending`, THE Search_API SHALL return that Paper with the Final Score marked `pending` and SHALL order such Papers after those with a computed Final Score.
5. IF a request supplies an empty, whitespace-only, or over-512-character query, THEN THE Search_API SHALL reject the request with a validation-error response and SHALL NOT perform a fetch.
6. IF every configured Source fails to return candidate records for a query, THEN THE Search_API SHALL return a response distinguishing a source-failure condition from a genuinely empty result set.
7. IF one configured Source fails while another succeeds, THEN THE Search_API SHALL return the Papers from the succeeding Source and SHALL NOT fail the whole search.

### Requirement 5: Asynchronous Scoring and Score Retrieval (Backend)

**User Story:** As the frontend application, I want scores computed
asynchronously and retrievable as they complete, so that search results appear
quickly and scores fill in afterward.

#### Acceptance Criteria

1. WHEN the Search_API caches the Papers for a search, THE Search_API SHALL schedule the Relevance_Assessment and the Reproducibility Score as asynchronous work using FastAPI BackgroundTasks and SHALL NOT block the search response on their completion.
2. WHILE a component score for a cached Paper has not yet been computed, THE Search_API SHALL report that component score with Score_Status `pending`.
3. WHEN an asynchronous score computation completes for a Paper, THE Search_API SHALL attach the resulting value to the cached Paper, recompute the Final Score from the available components, and update each affected Score_Status to `ready`.
4. IF an asynchronous score computation fails for a Paper, THEN THE Search_API SHALL record that component score as Score_Status `unavailable` for that Paper and SHALL NOT leave it `pending` indefinitely.
5. WHEN the Search_API receives a request for the current scores of one or more cached Papers by identifier, THE Search_API SHALL return each requested Paper's component scores and Final Score with their current Score_Status.
6. WHEN the Reproducibility Score component is provided by a stub rather than the `reproducibility-scoring` feature, THE Search_API SHALL still produce a Reproducibility Score value and a Final Score through the same Score_Status lifecycle, so that search and ranking function before `reproducibility-scoring` ships.
7. THE Search_API SHALL compute the Final Score as `0.7 · Relevance Score + 0.3 · Reproducibility Score`, reading both weights from configuration, and SHALL NOT derive the Final Score from the LLM.

### Requirement 6: Paper Detail Endpoint (Backend)

**User Story:** As the frontend application, I want an endpoint that returns a
single cached Paper, so that the detail view can show its full breakdown.

#### Acceptance Criteria

1. WHEN the Search_API receives a request for a Paper by its identifier and that Paper exists in the cache, THE Search_API SHALL return the Paper's title, authors, abstract, publication date, contributing Sources, external source links, repository link when present, Experiment Setup when present, and all component scores with their Score_Status.
2. IF the Search_API receives a request for a Paper identifier that is not in the cache, THEN THE Search_API SHALL return a not-found response.
3. WHEN a Paper has no associated repository link, THE Search_API SHALL return the repository link as absent rather than as an empty or placeholder value.
4. WHEN a Paper has no Experiment Setup yet, THE Search_API SHALL return the Experiment Setup as absent, since the Experiment Setup is produced by `reproducibility-scoring` and may not exist for this spec.
5. THE Search_API SHALL serve the Paper detail from the Postgres cache and SHALL NOT re-fetch from the external Sources on a detail request.

### Requirement 7: Source Fetch, Merge, and De-duplication (Business Logic)

**User Story:** As the backend, I want source adapters and a merge/de-duplication
step, so that OpenAlex and arXiv records become one unified, duplicate-free set
of Papers.

#### Acceptance Criteria

1. THE Search_System SHALL provide one Source_Adapter per configured Source (OpenAlex and arXiv), each issuing the query against its external index and mapping native records into the common pre-merge paper shape of title, authors, abstract, publication date, identifiers (DOI and/or arXiv id), source links, and repository link when the Source exposes one. Neither Source has a repository field, so an adapter takes it from the first GitHub link in the abstract (`find_repo_url`).
2. WHEN a Source_Adapter receives records from its Source, THE Source_Adapter SHALL restrict results to the Computer Science and Medicine domains per the configured source scope.
3. WHEN Merge_Dedup receives candidate records that share a normalized identifier (same DOI, or same arXiv id) or a matching normalized title with overlapping authors, THE Merge_Dedup SHALL collapse them into a single Paper that records every contributing Source and retains the richer non-empty value for each field.
4. WHEN Merge_Dedup produces a Paper from records of more than one Source, THE Merge_Dedup SHALL record every contributing Source on that Paper so that each is shown as a Source badge.
5. IF a Source_Adapter call fails or times out, THEN THE Merge_Dedup SHALL proceed with records from the remaining Source_Adapters and SHALL surface which Sources failed to the Search_API.
6. THE Source_Adapter SHALL request only index metadata and links and SHALL NOT fetch or store full text, consistent with the index-only rule.

### Requirement 8: LLM Query Assist and Relevance Assessment (Business Logic)

**User Story:** As the backend, I want the LLM to expand the query and to assess
each result's relevance, so that fetching is enriched and each Paper gets a
relevance score and blurb — while ranking stays non-AI.

#### Acceptance Criteria

1. WHEN Query_Assist is given a raw query, THE Query_Assist SHALL return an expanded query via Amazon Bedrock through LangChain, called from the backend, for the Search_API to fetch with.
2. IF Query_Assist fails or times out, THEN THE Search_System SHALL fall back to fetching with the Reader's original query rather than failing the search.
3. WHEN Relevance_Assessment is given a Paper and the query, THE Relevance_Assessment SHALL return a Relevance Score in the range 0 to 1 and a short natural-language relevance blurb via Amazon Bedrock through LangChain.
4. IF Relevance_Assessment fails for a Paper, THEN THE Search_System SHALL record that Paper's Relevance Score as Score_Status `unavailable` and SHALL NOT fabricate a Relevance Score.
5. WHEN the Final Score is computed, THE Search_System SHALL compute it as the configured non-AI blend `0.7 · Relevance Score + 0.3 · Reproducibility Score` and SHALL NOT ask the LLM to produce the Final Score or the ranking order.
6. THE Search_System SHALL read the Bedrock/LangChain configuration (model and credentials) from the environment and SHALL NOT read those values from committed source.

### Requirement 9: Paper Persistence and Schema (Backend)

**User Story:** As a developer of dependent features, I want the Paper cached
with a stable identity and the places scores and experiment setup will attach, so
that reproducibility-scoring and code-generation can build on it.

#### Acceptance Criteria

1. THE Search_API SHALL persist each cached Paper with a unique Paper identifier, its title, authors, abstract, publication date, contributing Sources, external identifiers (DOI and/or arXiv id), source links, and repository link when present, storing index metadata and links only and never full text.
2. THE Search_System SHALL introduce the Paper table through an Alembic migration committed under `backend/alembic/versions/`, and SHALL NOT create the Paper table through runtime schema generation (create_all).
3. THE Search_API SHALL store each Paper's Relevance Score, Reproducibility Score, Final Score, and each component's Score_Status on or alongside the cached Paper so that current scores are retrievable without recomputation.
4. WHEN Merge_Dedup identifies a candidate that matches a Paper already present in the cache, THE Search_API SHALL reuse the existing cached Paper rather than persisting a duplicate.
5. THE Search_API SHALL assign each Paper identifier at creation so that the identifier remains stable for the lifetime of the cached Paper and is referenceable by later features.
6. IF a required database, Bedrock, or source configuration value is absent from the environment variables at startup, THEN THE Search_System SHALL fail to start and SHALL NOT read that value from committed source.

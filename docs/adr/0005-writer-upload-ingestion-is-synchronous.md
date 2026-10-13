# Writer upload ingestion is synchronous, not a background job

For the `writer-workspace` feature, PDF manuscript text extraction and source
archive/Git unpacking run **synchronously inside the upload request** and return
the stored result, rather than following the `code-generation` start → poll →
fetch job pattern. We chose this because ingestion is seconds-long and bounded by
size and file-count caps (plus a server-side Git-fetch timeout), so the extra
moving parts of an async job (a job table, a poller, a status UI) are not earned.
The rejected alternative — reusing the `code-generation` `BackgroundTasks` job
lifecycle for consistency — was set aside as premature for short, bounded work.

## Consequences

- The upload endpoints return the stored artifact directly (`200` with the
  stored result), not a job id; this is the API contract shape dependent UI code
  relies on, and changing it later is a breaking change.
- A slow Git fetch holds the request open up to the client timeout (120s for
  source); the size/file-count caps and the fetch timeout bound this.
- If ingestion ever grows long (large repos, heavier extraction), it can move to
  the `BackgroundTasks` pattern `code-generation` already establishes — at the
  cost of that breaking contract change.

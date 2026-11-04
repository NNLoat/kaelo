# Demo mode records and replays at the three outside-world seams

A scripted live demo must show the same cards, scores and order every time, but
the app's results depend on three things we don't control: the Sources (OpenAlex,
arXiv), the LLM (Bedrock), and GitHub repo inspection. We decided that
`DEMO_MODE=record|replay` puts a record/replay **Cassette** (one committed JSON
file, `demo/fixtures/cassette.json`) at exactly those three seams, and the real
pipeline (merge, scoring, the deterministic roll-up, ranking) runs on top of the
recorded values. In `record`/`replay` the search response is also scored inline
and sorted by a total order, so it never returns stale or `pending` scores.

## Considered options

- **Canned response cards** (a fixture of finished results returned by the router):
  rejected because it demos a fake. Recording the inputs keeps the real scoring
  and ranking code on the stage.
- **Only turn off query expansion** (`QUERY_EXPANSION_ENABLED=false`): kept as a
  separate flag, but it fixes one source of drift; live sources, the LLM's own
  variance and GitHub still change the order.
- **Fixtures inside tests / a mock server:** rejected; the demo runs the real app
  in containers, so the seam has to live in the app.

## Consequences

- `off` is the default and never touches the Cassette; the normal app is unchanged.
- The Cassette holds source metadata, LLM prompts and responses, and repo signals
  only; secrets are refused at write time. It is committed deliberately by the
  presenter after reviewing `scripts/demo-record.sh`; nothing else writes it.
- Keys hash the seam's input, not the model id, so switching `BEDROCK_MODEL_ID`
  does not invalidate a recording. Changing a prompt template or a source query
  does: re-record.
- A replay miss falls back to live and logs a warning rather than failing the
  demo. Code generation is not recorded; the demo uses `CODEGEN_MOCK`.
- Record/replay is single-process and writes the file whole (not safe for
  concurrent writers); fine for a presenter, wrong for production.

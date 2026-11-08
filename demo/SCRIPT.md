# Live demo script

The demo runs in **replay**: every outside call (OpenAlex/arXiv, Bedrock, GitHub)
is answered from the committed Cassette `demo/fixtures/cassette.json`, so the same
query returns the same cards, scores and order every time, with no network or AWS
credentials. Scoring and ranking still run for real on top of the recorded values.

> **Say this:** "The results you're about to see are pre-recorded from the live
> sources, so the demo is repeatable; the scoring and ranking run for real."

## Settings

Set by `scripts/demo-env.sh`; you never edit `.env` for the demo.

| Setting | Value | Why |
| --- | --- | --- |
| `DEMO_MODE` | `replay` | answer from the Cassette (`demo-reset.sh` sets it) |
| `QUERY_EXPANSION_ENABLED` | `false` | no LLM query rewrite |
| `CODEGEN_MOCK` | `false` | code generation and review are real, answered from the Cassette |

## Before you present

1. `scripts/demo-reset.sh`: wipes the database, starts the stack in replay and
   registers the account `demo` / `demo-password` (local only, not a secret).
   Run it before every rehearsal and right before going on stage so paper ids and
   state start identical.
2. Open <http://localhost:5173> and log in as `demo`.
3. Optional: disconnect from the network to prove replay needs none.

## Queries (type them exactly, in this order)

| # | Query | Expected top results |
| --- | --- | --- |
| 1 | `Machine Learning Medical Image Segmentation Artificial Intelligence` | _fill in after the first record_ |

The frontend opens on **Relevance**. Show that order first; then click **Final
score**: the list must not reorder (the backend already returns Final Score order).
Review Reports are recorded for the pairs listed in `demo/generations.txt` (the MIScnn
paper, and the Writer's `demo/Iris3B-demo.pdf`); anything else you generate on stage
goes live and needs network and AWS.

## Re-record

Only when the queries change or the Cassette is stale. Needs network, AWS
credentials in `.env` and Bedrock access.

1. Edit `demo/queries.txt`.
2. `rm demo/fixtures/cassette.json` for a clean file (record keeps old entries).
3. `scripts/demo-record.sh` runs each query live (slow: scoring is inline), prints
   the ordered titles with Final Scores, then runs every job in
   `demo/generations.txt` (no UI clicks; each takes a minute or so). Review them.
4. Happy with the order? `git add demo/fixtures/cassette.json && git commit`.
   Fill in the expected-results column above.
5. `scripts/demo-reset.sh` and rehearse again in replay.

Nothing but `demo-record.sh` writes the Cassette. If a query isn't in it, replay
falls back to live and logs a warning; that means the Cassette needs re-recording.

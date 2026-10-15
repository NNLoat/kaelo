# Paper domain is captured at ingestion from the source's own classifier

A Paper's domain (Computer Science or Medicine) is read from the source's own
field classifier at ingestion — OpenAlex `primary_topic.field.id` (17 → Computer
Science, 27 → Medicine) and the arXiv category (`cs.*` → Computer Science,
`q-bio.*` → Medicine) — and persisted on the Paper as a new `domain` column,
carried through `SourceRecord` → `MergedPaper` → `Paper`. We need the domain to
select which reproducibility standard applies (ML Reproducibility Checklist for
CS, FAIR for Medicine — see ADR 0008). The signal already arrives in both source
responses but was previously discarded in each adapter's `_map`; we now keep it.
The alternative — inferring domain later from title/abstract with the LLM — was
rejected as slower, costlier, and less reliable than the source's own field tag,
which we are already filtering on.

## Consequences

- A new `domain` column on `papers` and a committed Alembic migration; the
  enum includes `unknown` for records whose source classifier is missing or
  ambiguous (e.g. a `q-bio` arXiv paper that straddles CS and Medicine).
- `arxiv_id` presence is **not** a domain proxy: arXiv is scoped to `cs.* OR
  q-bio.*`, and a merged Paper can carry both a DOI and an arXiv id, so domain
  must come from the classifier, not the identifier.
- When domain is `unknown`, scoring falls back to a domain-neutral baseline
  standard rather than guessing (see ADR 0008).

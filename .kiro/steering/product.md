# Product

## What we're building

An AI-assisted search engine for scientific papers that advances **open
science**: making research more accessible, transparent, and reproducible. It
finds papers, scores their reproducibility, and helps close the gap when a paper
ships without usable code.

## Who it's for

Researchers (not reviewers), in two roles:

- **Reader** — finds, reads, and evaluates others' papers.
- **Writer** — evaluates the reproducibility of their own paper.

## Core objectives

### Reader
- AI-assisted paper search.
- Reproducibility and code-quality scoring.
- Code generation for papers without a repository (off by default; opt-in).

### Writer
- Reproducibility and code-quality scoring.
- Code audit/generation for their paper's reproducibility.

## Out of scope (for now)

- Not hosting full-text papers and code repositories **from search/indexed
  sources** — for those we store only index/links. **Exception:** a Writer's own
  uploaded manuscript text and source code *are* stored (the User owns and
  consents to it). See `docs/adr/0003-writer-uploads-are-persisted.md`.
- Scientific papers only — not a general web search engine.
- Not executing or running generated code to verify it works.
- Not a peer-review/publishing platform (yet)

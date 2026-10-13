"""Property-based tests for Merge_Dedup (Hypothesis, >=100)."""

from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.merge import merge_dedup
from app.services.sources.base import SourceRecord

_sources = st.sampled_from(["openalex", "arxiv"])


def _record(source: str, doi: str, title: str, abstract: str | None = None):
    return SourceRecord(
        source=source,
        title=title,
        authors=["Ada Lovelace"],
        abstract=abstract,
        doi=doi,
    )


# Property 4: De-duplication merges same-publication records and keeps all sources.
# Validates: Requirements 7.3, 7.4
@settings(max_examples=100)
@given(
    dois=st.lists(st.integers(min_value=1, max_value=5), min_size=1, max_size=10),
    srcs=st.lists(_sources, min_size=10, max_size=10),
)
def test_dedup_merges_by_doi_and_keeps_sources(dois, srcs) -> None:
    records = [_record(srcs[i % len(srcs)], f"10.1/{d}", f"Paper {d}") for i, d in enumerate(dois)]
    merged = merge_dedup([records])

    # One MergedPaper per distinct DOI.
    assert len(merged) == len(set(dois))

    # Each merged paper's sources = exactly the sources of its contributing records.
    by_doi = {f"10.1/{d}": set() for d in dois}
    for i, d in enumerate(dois):
        by_doi[f"10.1/{d}"].add(srcs[i % len(srcs)])
    for m in merged:
        assert set(m.sources) == by_doi[m.doi]


# Property 5: Merge keeps the richer value and never fabricates full text.
# Validates: Requirements 7.3, 7.6, 9.1
@settings(max_examples=100)
@given(
    a=st.one_of(st.none(), st.text(max_size=40)),
    b=st.one_of(st.none(), st.text(max_size=200)),
)
def test_merge_keeps_richer_value_no_fabrication(a, b) -> None:
    r1 = _record("openalex", "10.1/x", "Shared Title", abstract=a)
    r2 = _record("arxiv", "10.1/x", "Shared Title", abstract=b)
    [merged] = merge_dedup([[r1, r2]])

    candidates = {v for v in (a, b) if v}
    if candidates:
        # The chosen abstract is one the adapters produced (never invented) and
        # is the longest non-empty one.
        assert merged.abstract in candidates
        assert len(merged.abstract) == max(len(c) for c in candidates)
    else:
        assert merged.abstract is None

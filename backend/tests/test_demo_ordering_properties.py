"""Property test for the demo ordering (spec demo-mode, task 6.3). Pure: no DB."""

import random
from dataclasses import dataclass

from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.paper import ScoreStatus
from app.services import ranking


@dataclass
class _P:
    id: int
    final_status: ScoreStatus
    final_score: float | None


def _frontend_final_sort(papers):
    """Mirror of frontend/src/components/useScorePolling.ts ``rankBy``/``sortCards``
    for the "final" key: value if ready else -1, descending, stable (Array.sort)."""

    def rank(p):
        return p.final_score if p.final_status == "ready" and p.final_score is not None else -1

    return sorted(papers, key=lambda p: -rank(p))


_scores = st.sampled_from([0.0, 0.25, 0.5, 1.0]) | st.floats(0.0, 1.0)
_papers = st.lists(
    st.tuples(st.sampled_from(list(ScoreStatus)), st.none() | _scores),
    max_size=12,
).map(lambda rows: [_P(i + 1, status, score) for i, (status, score) in enumerate(rows)])


# Feature: demo-mode, Property 11: Demo ordering is total, deterministic, a frontend fixed point
@settings(max_examples=100)
@given(papers=_papers, seed=st.integers())
def test_demo_ordering(papers, seed) -> None:
    ordered = ranking.sort_deterministic(papers)

    def is_ready(p):
        return p.final_status == "ready" and p.final_score is not None

    ready = [p for p in ordered if is_ready(p)]
    rest = [p for p in ordered if not is_ready(p)]
    assert ordered == ready + rest  # not-ready last
    assert ready == sorted(ready, key=lambda p: (-p.final_score, p.id))  # desc, id tie-break
    assert [p.id for p in rest] == sorted(p.id for p in rest)  # all not-ready tie on id

    shuffled = list(papers)
    random.Random(seed).shuffle(shuffled)
    assert ranking.sort_deterministic(shuffled) == ordered  # input order never matters

    assert _frontend_final_sort(ordered) == ordered  # switching to "Final score" reorders nothing

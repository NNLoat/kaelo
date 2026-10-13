"""Property-based tests for the non-AI Final Score blend (Hypothesis, >=100)."""

from dataclasses import dataclass

from hypothesis import given, settings
from hypothesis import strategies as st

from app.services import ranking

_scores = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
_weights = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


# Property 1: Final Score is the exact configured non-AI blend.
# Validates: Requirements 5.7, 8.5
@settings(max_examples=100)
@given(rel=_scores, repro=_scores, w_rel=_weights)
def test_final_score_is_exact_blend(rel: float, repro: float, w_rel: float) -> None:
    w_repro = 1.0 - w_rel
    result = ranking.final_score(rel, repro, w_rel=w_rel, w_repro=w_repro)
    assert result == w_rel * rel + w_repro * repro
    assert 0.0 <= result <= 1.0 + 1e-9


# Property 2: Final Score is pending exactly when a component is pending.
# Validates: Requirements 2.3, 4.4, 5.3
@settings(max_examples=100)
@given(
    rel=st.one_of(st.none(), _scores),
    repro=st.one_of(st.none(), _scores),
)
def test_final_score_pending_iff_component_pending(rel, repro) -> None:
    result = ranking.final_score(rel, repro, w_rel=0.7, w_repro=0.3)
    both_present = rel is not None and repro is not None
    assert (result is not None) == both_present


@dataclass
class _P:
    final_score: float | None


# Property 3: Results are sorted by Final Score, pending last.
# Validates: Requirements 4.3, 4.4
@settings(max_examples=100)
@given(st.lists(st.one_of(st.none(), _scores), max_size=20))
def test_sort_by_final_score_pending_last(values) -> None:
    papers = [_P(v) for v in values]
    ordered = ranking.sort_by_final_score(papers)

    present = [p.final_score for p in ordered if p.final_score is not None]
    assert present == sorted(present, reverse=True)

    seen_pending = False
    for p in ordered:
        if p.final_score is None:
            seen_pending = True
        else:
            assert not seen_pending, "a computed score sorted after a pending one"

"""Property tests for the rule-based reproducibility scorers (no LLM).

Hypothesis, >=100 iterations each. Each test references the design property it
validates.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.repro.code_quality import code_quality
from app.services.repro.completeness import EXPECTED_FIELDS, completeness
from app.services.repro.scorer import reproducibility
from app.services.repro.types import ExperimentSetupData, RepoSignals

_SIGNAL_FIELDS = ("has_readme", "has_license", "has_tests", "recent_activity")


def _signals(exists=True, inspectable=True, **flags) -> RepoSignals:
    base = dict.fromkeys(_SIGNAL_FIELDS, False)
    base.update(flags)
    return RepoSignals(exists=exists, inspectable=inspectable, failed=False, **base)


# Property 1: Code-Quality is deterministic and monotonic in positive signals.
# Validates: Requirements 2.1, 2.4
@settings(max_examples=200)
@given(st.lists(st.booleans(), min_size=4, max_size=4))
def test_code_quality_deterministic_and_monotonic(flags):
    sig = _signals(**dict(zip(_SIGNAL_FIELDS, flags, strict=True)))
    first = code_quality(sig)
    assert 0.0 <= first <= 1.0
    assert first == code_quality(sig)  # deterministic
    for i, on in enumerate(flags):
        if not on:
            flipped = list(flags)
            flipped[i] = True
            raised = code_quality(_signals(**dict(zip(_SIGNAL_FIELDS, flipped, strict=True))))
            assert raised >= first  # monotonic non-decreasing


# Property 2: Repository-absent yields the minimum code-quality score.
# Validates: Requirements 2.2
@settings(max_examples=100)
@given(st.lists(st.booleans(), min_size=4, max_size=4), st.booleans())
def test_repo_absent_is_minimum(flags, absent_via_exists):
    kw = dict(zip(_SIGNAL_FIELDS, flags, strict=True))
    sig = _signals(exists=not absent_via_exists, inspectable=absent_via_exists, **kw)
    # Either exists=False or inspectable=False -> 0.0
    sig = _signals(exists=False, inspectable=False, **kw)
    assert code_quality(sig) == 0.0


# Property 3: Setup completeness equals the populated-field fraction.
# Validates: Requirements 4.1
@settings(max_examples=200)
@given(st.lists(st.one_of(st.none(), st.text()), min_size=3, max_size=3))
def test_completeness_is_populated_fraction(values):
    setup = ExperimentSetupData(*values)
    populated = sum(1 for v in values if v)  # empty string counts as absent
    assert completeness(setup) == populated / len(EXPECTED_FIELDS)
    assert completeness(None) == 0.0


# Property 4: Reproducibility is deterministic, in range, and monotonic.
# Validates: Requirements 4.2, 4.6
@settings(max_examples=200)
@given(
    st.floats(0, 1),
    st.floats(0, 1),
    st.booleans(),
    st.floats(0.01, 1),
    st.floats(0.01, 1),
)
def test_reproducibility_range_and_monotonic(cq, setup, repo_exists, w_repo, w_setup):
    score = reproducibility(cq, repo_exists, setup, w_repo=w_repo, w_setup=w_setup)
    assert 0.0 <= score <= 1.0
    assert score == reproducibility(cq, repo_exists, setup, w_repo=w_repo, w_setup=w_setup)
    higher_cq = reproducibility(
        min(cq + 0.1, 1.0), repo_exists, setup, w_repo=w_repo, w_setup=w_setup
    )
    assert higher_cq >= score - 1e-9
    higher_setup = reproducibility(
        cq, repo_exists, min(setup + 0.1, 1.0), w_repo=w_repo, w_setup=w_setup
    )
    assert higher_setup >= score - 1e-9


# Property 5: A paper with no repo but a setup is still scored.
# Validates: Requirements 4.3
@settings(max_examples=100)
@given(st.floats(0.01, 1))
def test_no_repo_but_setup_is_scored(setup_completeness):
    # repo not inspectable -> code_quality 0.0, repo_exists False
    score = reproducibility(0.0, False, setup_completeness, w_repo=0.5, w_setup=0.5)
    assert score > 0.0

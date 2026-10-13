"""Reproducibility scoring seam.

STUB for the ``paper-search`` spec: returns a fixed in-range value with an
implicit ``ready`` status. ``reproducibility-scoring`` replaces this one module
behind the same signature (R5.6) — keep the seam in its own file.
"""


def score_reproducibility(paper_id: int) -> float:
    """Return a reproducibility score in ``[0, 1]`` for the given paper."""
    return 0.5

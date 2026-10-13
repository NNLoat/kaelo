"""The non-AI Final Score blend.

Pure arithmetic only — no LLM, HTTP, or DB imports anywhere in this module.
The LLM produces the Relevance Score and blurb; ranking never asks it for the
Final Score or the ordering (R5.7, R8.5).
"""


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def final_score(
    relevance: float | None,
    reproducibility: float | None,
    *,
    w_rel: float,
    w_repro: float,
) -> float | None:
    """Weighted blend of the two components.

    Returns ``w_rel*relevance + w_repro*reproducibility`` when both components
    are present, else ``None`` (-> Final Score pending). Inputs are clamped to
    ``[0, 1]``.
    """
    if relevance is None or reproducibility is None:
        return None
    return w_rel * _clamp01(relevance) + w_repro * _clamp01(reproducibility)


def sort_by_final_score(papers: list, key=lambda p: p.final_score) -> list:
    """Sort papers by Final Score descending, pending (None) ordered last.

    ``key`` extracts each paper's Final Score (``None`` => pending). Stable, so
    papers with equal/absent scores keep their input order.
    """
    return sorted(
        papers,
        key=lambda p: (key(p) is None, -(key(p) or 0.0)),
    )

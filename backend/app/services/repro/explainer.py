"""Score_Explainer — Bedrock via LangChain (R5). Prose only, never a number.

The already-computed ``score`` is a fixed input (R5.2); the prompt is built from
the computed Standard Result (the specific criteria that drove the score) and
the repo signals — no token or secret is ever included (Property 12). On failure
the caller proceeds without an explanation (R5.3).
"""

from langchain_aws import ChatBedrock

from app.core.config import get_settings
from app.services.demo.seams import CassetteChat, wrap_chat
from app.services.llm import _content_text
from app.services.repro.standards import CriterionStatus, StandardResult
from app.services.repro.types import RepoSignals

# How many of each list to feed the model, so the prompt stays bounded and the
# explanation focuses on what matters most. shortcut: fixed caps; revisit if
# the model needs more/less context for a good explanation.
_TOP_CATEGORIES = 3
_TOP_CRITERIA = 6
_TOP_DISCREPANCIES = 5


def _weak_criteria_lines(result: StandardResult) -> list[str]:
    """The unmet/partial criteria that actually cost points, with their notes."""
    weak = [
        r
        for r in result.results
        if r.status in (CriterionStatus.unmet, CriterionStatus.partial)
    ]
    # Heaviest first — those moved the score the most.
    weak.sort(key=lambda r: r.criterion.weight, reverse=True)
    lines = []
    for r in weak[:_TOP_CRITERIA]:
        note = r.evidence_note.strip() or "no evidence found"
        lines.append(f"- {r.criterion.title} ({r.status.value}): {note}")
    return lines


def _category_lines(result: StandardResult) -> list[str]:
    """The display categories that lost the most points."""
    ranked = sorted(result.categories, key=lambda c: c.points_lost, reverse=True)
    return [
        f"- {c.category}: scored {c.score:.2f} (lost {c.points_lost:.2f})"
        for c in ranked[:_TOP_CATEGORIES]
        if c.points_lost > 0
    ]


def _discrepancy_lines(result: StandardResult) -> list[str]:
    """Paper-to-code contradictions the standard flagged."""
    lines = []
    for r in result.discrepancies[:_TOP_DISCREPANCIES]:
        paper = r.paper_value or "unspecified"
        code = r.code_value or "unspecified"
        lines.append(f"- {r.criterion.title}: paper says {paper}, code says {code}")
    return lines


def explain(score: float, signals: RepoSignals, result: StandardResult) -> str:
    """Short prose grounded in the specific criteria behind a fixed score.

    ``score`` is fixed (R5.2); the prompt references the Standard Result's
    weakest categories, the specific unmet/partial criteria with their evidence
    notes, and any paper-to-code discrepancies, so the explanation is specific
    to this paper rather than a generic checklist.
    """
    categories = _category_lines(result)
    weak = _weak_criteria_lines(result)
    discrepancies = _discrepancy_lines(result)

    parts = [
        "In three or four sentences, explain this reproducibility score to a "
        "researcher deciding whether to build on the paper. Be specific: name "
        "the concrete gaps below and what they mean for reproducing the work. "
        "Do NOT restate the score as a different number, do NOT recompute it, "
        "and do NOT output a heading or title — reply with the explanation prose "
        "only.",
        f"Reproducibility score (0-1, fixed): {score:.2f}",
        f"Evaluated against: {result.standard_key} (field: {result.field_of_study})",
        f"Repository exists: {signals.exists}; has README: {signals.has_readme}; "
        f"has license: {signals.has_license}; has tests: {signals.has_tests}; "
        f"recent activity: {signals.recent_activity}",
    ]
    if categories:
        parts.append("Weakest areas (category: score, points lost):\n" + "\n".join(categories))
    if weak:
        parts.append("Specific gaps (criterion: evidence):\n" + "\n".join(weak))
    if discrepancies:
        parts.append(
            "Paper-to-code discrepancies:\n" + "\n".join(discrepancies)
        )

    resp = _client().invoke("\n\n".join(parts))
    return _content_text(resp).strip()


def _client() -> ChatBedrock | CassetteChat:
    settings = get_settings()
    return wrap_chat(
        lambda: ChatBedrock(model=settings.bedrock_model_id, region_name=settings.aws_region)
    )

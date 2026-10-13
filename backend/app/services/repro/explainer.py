"""Score_Explainer — Bedrock via LangChain (R5). Prose only, never a number.

The already-computed ``score`` is a fixed input (R5.2); the prompt is built from
the computed signals and completeness only — no token or secret is ever included
(Property 12). On failure the caller proceeds without an explanation (R5.3).
"""

from langchain_aws import ChatBedrock

from app.core.config import get_settings
from app.services.llm import _content_text
from app.services.repro.types import RepoSignals


def _client() -> ChatBedrock:
    settings = get_settings()
    return ChatBedrock(model=settings.bedrock_model_id, region_name=settings.aws_region)


def explain(score: float, signals: RepoSignals, completeness: float) -> str:
    """Short prose referencing the signals behind a fixed score."""
    prompt = (
        "In two or three sentences, explain this reproducibility score to a "
        "researcher. The score is fixed; do not recompute or restate it as a "
        "different number. Reference the signals below.\n\n"
        f"Reproducibility score (0-1): {score:.2f}\n"
        f"Repository exists: {signals.exists}\n"
        f"Repository inspectable: {signals.inspectable}\n"
        f"Has README: {signals.has_readme}\n"
        f"Has license: {signals.has_license}\n"
        f"Has tests: {signals.has_tests}\n"
        f"Recent activity: {signals.recent_activity}\n"
        f"Experiment-setup completeness (0-1): {completeness:.2f}"
    )
    resp = _client().invoke(prompt)
    return _content_text(resp).strip()

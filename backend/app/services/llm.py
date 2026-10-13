"""Query_Assist and Relevance_Assessment via Amazon Bedrock (LangChain).

No ranking logic lives here (R8.5). ``expand_query`` falls back to the raw query
on failure (caller's responsibility); ``assess_relevance`` raises on failure so
the orchestrator records relevance ``unavailable`` rather than fabricating a
value (R8.4).
"""

import json
import re
from dataclasses import dataclass
from functools import lru_cache

from langchain_aws import ChatBedrock

from app.core.config import get_settings


@dataclass
class PaperSummary:
    title: str
    abstract: str | None


@dataclass
class RelevanceResult:
    score: float  # 0..1
    blurb: str


@lru_cache
def _client() -> ChatBedrock:
    settings = get_settings()
    return ChatBedrock(
        model=settings.bedrock_model_id,
        region_name=settings.aws_region,
    )


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def expand_query(raw: str) -> str:
    """Enrich the raw query for better retrieval.

    On any failure the caller falls back to ``raw`` (R8.2), so this raises and
    the caller is expected to catch it.
    """
    prompt = (
        "Rewrite this scientific-paper search query to improve retrieval. "
        "Add synonyms and related terms. Reply with only the rewritten query.\n\n"
        f"Query: {raw}"
    )
    resp = _client().invoke(prompt)
    text = _content_text(resp).strip()
    return text or raw


def assess_relevance(paper: PaperSummary, query: str) -> RelevanceResult:
    """Score a paper's relevance to the query and write a short blurb.

    Raises on failure (R8.4). Score is clamped to ``[0, 1]``.
    """
    prompt = (
        "Rate how relevant this paper is to the query on a 0.0-1.0 scale and "
        "give a one-sentence blurb. Reply as JSON: "
        '{"score": <float>, "blurb": "<text>"}.\n\n'
        f"Query: {query}\n"
        f"Title: {paper.title}\n"
        f"Abstract: {paper.abstract or '(none)'}"
    )
    resp = _client().invoke(prompt)
    text = _content_text(resp)

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"relevance response not JSON: {text!r}")
    data = json.loads(match.group(0))
    return RelevanceResult(
        score=_clamp01(float(data["score"])),
        blurb=str(data["blurb"]),
    )


def _content_text(resp) -> str:
    content = getattr(resp, "content", resp)
    if isinstance(content, str):
        return content
    # LangChain may return a list of content blocks.
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block) for block in content
        )
    return str(content)

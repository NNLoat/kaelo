"""Search pipeline and async scoring orchestration.

``run_search`` fetches/merges/caches papers; ``schedule_scoring`` queues one
background job per paper; ``run_scoring_for_paper`` computes relevance (LLM) and
reproducibility (stub), attaches each with a terminal status, and recomputes the
Final Score. No component is ever left ``pending`` after its job runs (R5.3/5.4).
"""

from dataclasses import dataclass

from fastapi import BackgroundTasks
from sqlmodel import Session, select

from app.core.config import get_settings
from app.db.session import engine
from app.models.paper import Paper, PaperDomain, ScoreStatus
from app.services import ranking
from app.services.demo.seams import wrap_source
from app.services.llm import PaperSummary, assess_relevance, expand_query
from app.services.merge import MergedPaper, merge_dedup
from app.services.reproducibility import score_reproducibility
from app.services.sources.arxiv import ArxivAdapter
from app.services.sources.base import SourceAdapter, SourceError
from app.services.sources.openalex import OpenAlexAdapter

# One adapter per Source. Kept here so the pipeline fans out over them.
_ADAPTERS: list[SourceAdapter] = [OpenAlexAdapter(), ArxivAdapter()]


@dataclass
class SearchResult:
    paper_ids: list[int]
    failed_sources: list[str]
    all_failed: bool


def _adapters() -> list[SourceAdapter]:
    return [wrap_source(a) for a in _ADAPTERS]


def run_search(query: str, session: Session) -> SearchResult:
    """Expand, fan out to adapters, merge, and upsert into the papers cache.

    Returns the cached paper ids and the set of failed sources. ``all_failed``
    is True only when every adapter raised, so the caller can return 502
    distinctly from an empty-but-successful result (R4.6, R4.7).
    """
    settings = get_settings()

    effective_query = query  # fall back to the raw query on failure (R8.2)
    if settings.query_expansion_enabled:
        try:
            effective_query = expand_query(query)
        except Exception:
            pass

    groups: list[list] = []
    failed: list[str] = []
    adapters = _adapters()
    for adapter in adapters:
        try:
            records = adapter.fetch(
                effective_query,
                limit=settings.source_result_limit,
                timeout=settings.source_timeout_seconds,
            )
            groups.append(records)
        except SourceError:
            failed.append(adapter.name)

    all_failed = len(failed) == len(adapters)
    if all_failed:
        return SearchResult(paper_ids=[], failed_sources=failed, all_failed=True)

    merged = merge_dedup(groups)
    paper_ids = [_upsert(m, session) for m in merged]
    session.commit()
    return SearchResult(paper_ids=paper_ids, failed_sources=failed, all_failed=False)


def _upsert(merged: MergedPaper, session: Session) -> int:
    """Reuse an existing row by DOI else arXiv id, else insert (R9.4)."""
    existing: Paper | None = None
    if merged.doi:
        existing = session.exec(select(Paper).where(Paper.doi == merged.doi)).first()
    if existing is None and merged.arxiv_id:
        existing = session.exec(select(Paper).where(Paper.arxiv_id == merged.arxiv_id)).first()

    if existing is not None:
        # Merge any newly-contributing sources; keep existing scores.
        for src in merged.sources:
            if src not in existing.sources:
                existing.sources = existing.sources + [src]
        existing.repo_url = existing.repo_url or merged.repo_url
        if existing.domain is PaperDomain.unknown and merged.domain is not PaperDomain.unknown:
            existing.domain = merged.domain
        session.add(existing)
        session.flush()
        return existing.id

    paper = Paper(
        title=merged.title,
        authors=merged.authors,
        abstract=merged.abstract,
        published_date=merged.published_date,
        doi=merged.doi,
        arxiv_id=merged.arxiv_id,
        sources=merged.sources,
        source_links=[{"source": s, "url": u} for s, u in merged.source_links],
        repo_url=merged.repo_url,
        domain=merged.domain,
    )
    session.add(paper)
    session.flush()
    return paper.id


def schedule_scoring(paper_ids: list[int], query: str, tasks: BackgroundTasks) -> None:
    """Queue one background scoring job per paper (R5.1)."""
    for pid in paper_ids:
        tasks.add_task(run_scoring_for_paper, pid, query)


def score_inline(paper_ids: list[int], query: str) -> None:
    """Score each paper to completion, in order (demo record/replay)."""
    for pid in paper_ids:
        run_scoring_for_paper(pid, query)


def run_scoring_for_paper(paper_id: int, query: str) -> None:
    """Compute and persist the component scores for one paper.

    Opens its own Session (runs after the request session closes). Every
    component ends ``ready`` or ``unavailable`` — never ``pending`` (R5.3/5.4).
    """
    settings = get_settings()
    with Session(engine) as session:
        paper = session.get(Paper, paper_id)
        if paper is None:
            return

        # Relevance via the LLM; failure => unavailable, never fabricated (R8.4).
        try:
            result = assess_relevance(
                PaperSummary(title=paper.title, abstract=paper.abstract), query
            )
            paper.relevance_score = result.score
            paper.relevance_blurb = result.blurb
            paper.relevance_status = ScoreStatus.ready
        except Exception:
            paper.relevance_score = None
            paper.relevance_status = ScoreStatus.unavailable

        # Reproducibility via the stub seam (R5.6).
        try:
            paper.reproducibility_score = score_reproducibility(paper_id)
            paper.reproducibility_status = ScoreStatus.ready
        except Exception:
            paper.reproducibility_score = None
            paper.reproducibility_status = ScoreStatus.unavailable

        value = ranking.final_score(
            paper.relevance_score,
            paper.reproducibility_score,
            w_rel=settings.relevance_weight,
            w_repro=settings.reproducibility_weight,
        )
        paper.final_score = value
        paper.final_status = ScoreStatus.ready if value is not None else ScoreStatus.unavailable

        session.add(paper)
        session.commit()

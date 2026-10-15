"""Search_API router: /api/papers search, scores, and detail endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.paper import Paper, PaperRead, ReproducibilityBreakdown, ScoreCell, ScoreStatus
from app.models.reproducibility import ReproducibilityScore
from app.services import ranking, scoring

router = APIRouter(prefix="/api/papers", tags=["papers"])

_MAX_QUERY_LEN = 512

# Display labels for the selected Reproducibility Standard (R8.8).
_STANDARD_NAMES = {
    "ml_checklist": "ML Reproducibility Checklist",
    "fair": "FAIR",
    "baseline": "Baseline",
}


class SearchRequest(BaseModel):
    query: str

    @field_validator("query")
    @classmethod
    def _validate(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped or len(v) > _MAX_QUERY_LEN:
            raise ValueError("query must be non-empty and <= 512 characters")
        return v


class PaperCard(BaseModel):
    id: int
    title: str
    authors: list[str]
    sources: list[str]
    relevance: ScoreCell
    reproducibility: ScoreCell
    final: ScoreCell
    blurb: str | None


class SearchResponse(BaseModel):
    papers: list[PaperCard]
    failed_sources: list[str]


class ScoreSummary(BaseModel):
    relevance: ScoreCell
    reproducibility: ScoreCell
    final: ScoreCell
    blurb: str | None


def _cell(value: float | None, status: ScoreStatus) -> ScoreCell:
    return ScoreCell(status=status, value=value)


def _card(paper: Paper) -> PaperCard:
    return PaperCard(
        id=paper.id,
        title=paper.title,
        authors=paper.authors,
        sources=paper.sources,
        relevance=_cell(paper.relevance_score, paper.relevance_status),
        reproducibility=_cell(paper.reproducibility_score, paper.reproducibility_status),
        final=_cell(paper.final_score, paper.final_status),
        blurb=paper.relevance_blurb,
    )


@router.post("/search", response_model=SearchResponse)
def search(
    payload: SearchRequest,
    tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> SearchResponse:
    result = scoring.run_search(payload.query, session)

    if result.all_failed:
        raise HTTPException(
            status_code=502,
            detail={"detail": "all sources failed", "source_failure": True},
        )

    scoring.schedule_scoring(result.paper_ids, payload.query, tasks)

    papers = [session.get(Paper, pid) for pid in result.paper_ids]
    ordered = ranking.sort_by_final_score([p for p in papers if p is not None])
    return SearchResponse(
        papers=[_card(p) for p in ordered],
        failed_sources=result.failed_sources,
    )


@router.get("/scores")
def scores(
    ids: str = Query(..., description="Comma-separated paper ids"),
    session: Session = Depends(get_session),
) -> dict[int, ScoreSummary]:
    try:
        wanted = [int(x) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=422, detail="ids must be integers") from None

    out: dict[int, ScoreSummary] = {}
    for pid in wanted:
        paper = session.get(Paper, pid)
        if paper is None:
            continue  # omit unknown ids
        out[pid] = ScoreSummary(
            relevance=_cell(paper.relevance_score, paper.relevance_status),
            reproducibility=_cell(paper.reproducibility_score, paper.reproducibility_status),
            final=_cell(paper.final_score, paper.final_status),
            blurb=paper.relevance_blurb,
        )
    return out


@router.get("/{paper_id}", response_model=PaperRead)
def get_paper(paper_id: int, session: Session = Depends(get_session)) -> PaperRead:
    paper = session.get(Paper, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="paper not found")

    row = session.exec(
        select(ReproducibilityScore).where(ReproducibilityScore.paper_id == paper_id)
    ).first()
    breakdown = None
    if row is not None:
        breakdown = ReproducibilityBreakdown(
            code_quality=_cell(row.code_quality_score, row.status),
            setup_completeness=_cell(row.setup_completeness, row.status),
            repo_exists=row.repo_exists,
            explanation=row.explanation,
            standard_key=row.standard_key,
            standard_name=_STANDARD_NAMES.get(row.standard_key),
            criteria=row.criteria,
        )

    return PaperRead(
        **paper.model_dump(
            include={
                "id",
                "title",
                "authors",
                "abstract",
                "published_date",
                "doi",
                "arxiv_id",
                "sources",
                "source_links",
                "repo_url",
                "experiment_setup",
            }
        ),
        relevance=_cell(paper.relevance_score, paper.relevance_status),
        reproducibility=_cell(paper.reproducibility_score, paper.reproducibility_status),
        final=_cell(paper.final_score, paper.final_status),
        blurb=paper.relevance_blurb,
        reproducibility_breakdown=breakdown,
    )

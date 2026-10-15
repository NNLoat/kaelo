from datetime import UTC, date, datetime
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class ScoreStatus(str, Enum):
    pending = "pending"
    ready = "ready"
    unavailable = "unavailable"


class PaperDomain(str, Enum):
    """Field domain captured at ingestion; selects the Reproducibility Standard (R9.4)."""

    computer_science = "computer_science"
    medicine = "medicine"
    unknown = "unknown"


class ScoreCell(BaseModel):
    """Clean read shape for one component score — never leaks raw columns."""

    status: ScoreStatus
    value: float | None


class ReproducibilityBreakdown(BaseModel):
    """Detail-view breakdown from the reproducibility_scores row (R8.1/8.6/8.7).

    Additive and nullable: ``null`` when reproducibility-scoring hasn't run, so
    paper-search's existing detail reads are unaffected.
    """

    code_quality: ScoreCell
    setup_completeness: ScoreCell
    repo_exists: bool | None
    explanation: str | None
    standard_key: str | None = None
    standard_name: str | None = None  # display label derived from standard_key
    criteria: list[dict] | None = None  # per-Criterion: {id, title, status, evidence_note}


class PaperBase(SQLModel):
    title: str = Field(index=True, max_length=1024)
    authors: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    abstract: str | None = Field(default=None)  # index metadata only (R7.6)
    published_date: date | None = Field(default=None)
    doi: str | None = Field(default=None, index=True)
    arxiv_id: str | None = Field(default=None, index=True)
    sources: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    source_links: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    repo_url: str | None = Field(default=None)  # None => no repo (R6.3)
    domain: PaperDomain = Field(default=PaperDomain.unknown)  # selects standard (R9.4)


class Paper(PaperBase, table=True):
    __tablename__ = "papers"

    id: int | None = Field(default=None, primary_key=True)

    # Per-component scores + statuses (R9.3).
    relevance_score: float | None = Field(default=None)
    relevance_status: ScoreStatus = Field(default=ScoreStatus.pending)
    relevance_blurb: str | None = Field(default=None)
    reproducibility_score: float | None = Field(default=None)
    reproducibility_status: ScoreStatus = Field(default=ScoreStatus.pending)
    final_score: float | None = Field(default=None)
    final_status: ScoreStatus = Field(default=ScoreStatus.pending)

    # Experiment Setup is produced by reproducibility-scoring; absent here (R6.4).
    experiment_setup: dict | None = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)


class PaperRead(PaperBase):
    id: int
    relevance: ScoreCell
    reproducibility: ScoreCell
    final: ScoreCell
    blurb: str | None
    experiment_setup: dict | None
    reproducibility_breakdown: ReproducibilityBreakdown | None = None

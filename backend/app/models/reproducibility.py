from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.paper import ScoreStatus  # reuse the shared enum


class ReproducibilityScore(SQLModel, table=True):
    __tablename__ = "reproducibility_scores"

    id: int | None = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="papers.id", unique=True, index=True)  # R7.4

    score: float | None = Field(default=None)  # the number (R7.1)
    status: ScoreStatus = Field(default=ScoreStatus.pending)
    code_quality_score: float | None = Field(default=None)
    repo_exists: bool | None = Field(default=None)
    repo_inspectable: bool | None = Field(default=None)
    setup_completeness: float | None = Field(default=None)
    explanation: str | None = Field(default=None)  # nullable (R5.3)

    # Selected Reproducibility Standard + per-Criterion results (R7.1, R8.8, R10).
    # Both additive/nullable: null until the scoring seam populates them (task 13.2).
    standard_key: str | None = Field(default=None)  # e.g. "ml_checklist" / "fair" / "baseline"
    criteria: list[dict] | None = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)


class ExperimentSetup(SQLModel, table=True):
    __tablename__ = "experiment_setups"

    id: int | None = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="papers.id", unique=True, index=True)  # R7.4

    hyperparameters: str | None = Field(default=None)  # None => absent (R7.2)
    datasets: str | None = Field(default=None)
    environment: str | None = Field(default=None)
    available: bool = Field(default=False)  # False => extraction unavailable (R3.3)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)

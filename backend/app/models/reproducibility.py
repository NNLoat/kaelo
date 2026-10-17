from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.paper import ScoreStatus  # reuse the shared enum


class ReproducibilityScore(SQLModel, table=True):
    __tablename__ = "reproducibility_scores"

    id: int | None = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="papers.id", unique=True, index=True)  # R7.4

    score: float | None = Field(default=None)  # the weighted roll-up S (R7.1)
    status: ScoreStatus = Field(default=ScoreStatus.pending)
    code_quality_score: float | None = Field(default=None)
    repo_exists: bool | None = Field(default=None)
    repo_inspectable: bool | None = Field(default=None)
    setup_completeness: float | None = Field(default=None)
    explanation: str | None = Field(default=None)  # nullable (R5.3)

    # Standards-Conformance model fields from scoring_rule.md v1.2 (R4, R7.1, R8.8, R10).
    # Additive/nullable: null until the scoring seam populates them.
    field_of_study: str | None = Field(default=None)  # "medicine" / "computer_science" / "unknown"
    standard_key: str | None = Field(
        default=None
    )  # e.g. "tripod_ai" / "cs_merged" / "baseline"
    score_q: float | None = Field(default=None)  # S_Q, the Q-group (0.30) sub-score
    score_d: float | None = Field(default=None)  # S_D, the D + Q/D group (0.70) sub-score
    # Full per-Criterion Standard Result. Each dict carries: id, title, tag
    # ("Q"/"D"/"Q/D"), weight, category, source_references, status
    # ("met"/"partial"/"unmet"/"not_applicable"), confidence, evidence_note.
    criteria: list[dict] | None = Field(default=None, sa_column=Column(JSON))
    # Seven per-display-category rows: {category, score, points_lost}.
    categories: list[dict] | None = Field(default=None, sa_column=Column(JSON))
    # Discrepancy report: D criteria scored 0 by contradiction
    # {criterion_id, paper_value, code_value, reference}.
    discrepancies: list[dict] | None = Field(default=None, sa_column=Column(JSON))
    # Reference versions scored against, per scoring_rule.md §8 (e.g.
    # {"scoring_rule": "1.2", "tripod_ai": "2024", "acm": "v1.1", ...}).
    reference_versions: dict | None = Field(default=None, sa_column=Column(JSON))

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

"""GenerationJob + Generation tables (R8).

Jobs track the async lifecycle; Generations hold the derived artifact. Both are
owner-scoped. ``paper_ref`` is the Paper's index identifier as a string (the
frontend contract) — never full text (R8.5). Files are stored as a JSON list of
{path, content}; only derived/generated text is persisted.
"""

import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.core.codegen import Case  # reuse the single Case enum


class JobState(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    refused = "refused"


class GenerationJob(SQLModel, table=True):
    __tablename__ = "generation_jobs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)  # R4.1 ownership
    paper_ref: str = Field(index=True, max_length=255)  # index id only (R8.5)
    case: Case = Field()
    state: JobState = Field(default=JobState.pending, index=True)
    reason: str | None = Field(default=None)  # refused reason (R4.3-R4.5)
    generation_id: uuid.UUID | None = Field(default=None, foreign_key="generations.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)


class Generation(SQLModel, table=True):
    __tablename__ = "generations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)  # R3.1 visibility
    paper_ref: str = Field(index=True, max_length=255)  # index id only (R8.5)
    case: Case = Field()
    files: list[dict] = Field(sa_column=Column(JSON))  # [{path, content}] derived only (R8.5)
    code_quality_score: float = Field()  # artifact score (R8.3, ADR-0004)
    code_quality_rationale: str = Field()
    disclaimer: str = Field()
    is_latest: bool = Field(default=True, index=True)  # latest per (owner,paper,case) (R5.6)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)


class JobCreate(SQLModel):
    paper_ref: str
    case: Case


class JobRead(SQLModel):
    id: uuid.UUID
    paper_ref: str
    case: Case
    state: JobState
    reason: str | None = None
    generation_id: uuid.UUID | None = None


class GenerationRead(SQLModel):
    id: uuid.UUID
    paper_ref: str
    case: Case
    files: list[dict]
    code_quality_score: float
    code_quality_rationale: str
    disclaimer: str
    is_latest: bool
    created_at: datetime

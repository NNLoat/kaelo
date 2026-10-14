"""Writer-owned claim + uploads (R9).

A ``PaperClaim`` is the owning record for a Writer's claimed paper; it carries at
most one ``WriterManuscript`` (extracted text + original filename) and a set of
``WriterSourceFile`` rows (one ``(path, content)`` per stored text file). This is
the persisted Writer-owned content carve-out from the index-only rule (ADR-0003):
we store derived text only — never the raw PDF or archive bytes.

Constraints enforced here (and in the migration, task 3.2):
- unique ``(owner_id, paper_ref_normalized)`` — one claim per Writer per paper
  (R5.3, R9.3);
- unique ``writer_manuscripts.claim_id`` — at most one manuscript per claim (R9.4);
- unique ``(claim_id, path)`` in ``writer_source_files`` — one row per file (R9.5).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class PaperClaim(SQLModel, table=True):
    __tablename__ = "paper_claims"
    __table_args__ = (UniqueConstraint("owner_id", "paper_ref_normalized"),)  # R5.3, R9.3

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)  # R5.1 ownership
    paper_ref_normalized: str = Field(index=True, max_length=512)  # canonical (R5.1)
    paper_ref_original: str = Field(max_length=1024)  # as supplied (R5.6)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)


class WriterManuscript(SQLModel, table=True):
    __tablename__ = "writer_manuscripts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    claim_id: uuid.UUID = Field(
        foreign_key="paper_claims.id", index=True, unique=True
    )  # one per claim (R9.4)
    filename: str = Field(max_length=512)  # original filename (R6.1)
    text: str = Field()  # extracted text only; no raw PDF (R6.7)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)


class WriterSourceFile(SQLModel, table=True):
    __tablename__ = "writer_source_files"
    __table_args__ = (UniqueConstraint("claim_id", "path"),)  # one row per file (R9.5)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    claim_id: uuid.UUID = Field(foreign_key="paper_claims.id", index=True)
    path: str = Field(max_length=1024)  # relative path, unique per claim (R9.5)
    content: str = Field()  # decodable text only; no raw archive (R7.8, R10.6)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)


# --- Read schemas (API contracts; owner scoping enforced in handlers) ---


class ClaimRead(SQLModel):
    id: uuid.UUID
    paper_ref: str  # original supplied reference
    paper_ref_normalized: str
    has_manuscript: bool
    has_source: bool
    created_at: datetime


class ManuscriptRead(SQLModel):
    filename: str
    present: bool = True


class SourceRead(SQLModel):
    paths: list[str]
    skipped_paths: list[str]  # binaries dropped during unpack (R10.6)


class ClaimDetail(ClaimRead):
    manuscript: ManuscriptRead | None = None
    source_paths: list[str] = []

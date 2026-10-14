"""Codegen_API — job lifecycle + endpoints (R4, R5, R6, R8).

Async generation runs on FastAPI BackgroundTasks (no broker; see design). The
start endpoint persists a job and schedules ``run_job``; the client polls. All
reads/deletes are owner-scoped (cross-user -> 404, R6.5) and require a session
(R4.6, R6.6). The artifact score lives only on the Generation row — this feature
never writes a Paper's reproducibility score (R5.8, ADR-0004).
"""

import io
import zipfile
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core import codegen as helper
from app.core.codegen import Case, GenerationError, GenerationInputs
from app.core.config import get_settings
from app.core.session import current_user
from app.db.session import engine, get_session
from app.models.generation import (
    Generation,
    GenerationJob,
    GenerationRead,
    JobCreate,
    JobRead,
    JobState,
)
from app.models.paper import Paper
from app.models.reproducibility import ExperimentSetup
from app.models.user import User
from app.models.writer import PaperClaim, WriterManuscript, WriterSourceFile
from app.routers.writer import normalize_reference

router = APIRouter(prefix="/api/codegen", tags=["codegen"])

DISCLAIMER = "Unverified, machine-generated code. It was not executed, compiled, or verified."
_INFLIGHT = (JobState.pending, JobState.running)


# --- input loading / preconditions -------------------------------------------


def _paper_for_ref(session: Session, paper_ref: str) -> Paper | None:
    """Resolve the string paper_ref to a Paper (integer PK), or None."""
    try:
        pid = int(paper_ref)
    except (TypeError, ValueError):
        return None
    return session.get(Paper, pid)


def _setup_text(session: Session, paper: Paper | None) -> str | None:
    """The Experiment_Setup text for a paper, or None if absent/unavailable."""
    if paper is None:
        return None
    row = session.exec(
        select(ExperimentSetup).where(ExperimentSetup.paper_id == paper.id)
    ).first()
    if row is None or not row.available:
        return None
    parts = [p for p in (row.hyperparameters, row.datasets, row.environment) if p]
    return "\n".join(parts) or None


def _precondition(
    session: Session, case: Case, paper_ref: str, owner_id: int
) -> tuple[str | None, GenerationInputs | None]:
    """Return (refusal_reason, inputs). Reason set => refuse, inputs is None
    (R4.3-R4.5); reason None => inputs is ready for the helper."""
    paper = _paper_for_ref(session, paper_ref)
    setup = _setup_text(session, paper)

    if case in (Case.generate, Case.align):
        if setup is None:
            return (
                "No experiment setup for this paper yet, so there's nothing to generate from.",
                None,
            )
    if case is Case.align:
        if paper is None or not paper.repo_url:
            return ("This paper has no repository to align with.", None)
        return (None, GenerationInputs(experiment_setup=setup, repo_link=paper.repo_url))
    if case is Case.writer:
        return _writer_inputs(session, paper_ref, owner_id)
    return (None, GenerationInputs(experiment_setup=setup))


def _writer_inputs(
    session: Session, paper_ref: str, owner_id: int
) -> tuple[str | None, GenerationInputs | None]:
    """Resolve a Writer's uploaded manuscript + source for a claimed paper.

    Refuse (R4.5) when there is no claim or no uploaded manuscript. Otherwise
    build inputs from the stored text: manuscript text drives the experiment
    setup (we do not fabricate an ExperimentSetup row), and the uploaded source
    files — if any — are joined so the helper refines rather than generates from
    scratch (R5.3).
    """
    _NO_UPLOAD = "No uploaded manuscript for this paper yet, so there's nothing to generate from."
    normalized = normalize_reference(paper_ref)
    if normalized is None:
        return (_NO_UPLOAD, None)
    claim = session.exec(
        select(PaperClaim).where(
            PaperClaim.owner_id == owner_id,
            PaperClaim.paper_ref_normalized == normalized,
        )
    ).first()
    if claim is None:
        return (_NO_UPLOAD, None)
    manuscript = session.exec(
        select(WriterManuscript).where(WriterManuscript.claim_id == claim.id)
    ).first()
    if manuscript is None:
        return (_NO_UPLOAD, None)

    sources = session.exec(
        select(WriterSourceFile)
        .where(WriterSourceFile.claim_id == claim.id)
        .order_by(WriterSourceFile.path)  # type: ignore[arg-type]
    ).all()
    uploaded_source = (
        "\n\n".join(f"=== {f.path} ===\n{f.content}" for f in sources) if sources else None
    )
    return (
        None,
        GenerationInputs(
            experiment_setup=manuscript.text,
            manuscript_text=manuscript.text,
            uploaded_source=uploaded_source,
        ),
    )


# --- worker -------------------------------------------------------------------


def run_job(job_id: UUID) -> None:
    """Execute a scheduled job in its own session (R5). Sets running, loads
    inputs, calls the helpers, persists a Generation (flipping the prior latest),
    sets succeeded; any helper error -> failed, no Generation persisted (R5.7)."""
    with Session(engine) as session:
        job = session.get(GenerationJob, job_id)
        if job is None or job.state is not JobState.pending:
            return
        job.state = JobState.running
        job.updated_at = datetime.now(UTC)
        session.add(job)
        session.commit()

        reason, inputs = _precondition(session, job.case, job.paper_ref, job.owner_id)
        if inputs is None:
            # Preconditions passed at start but no longer hold (e.g. setup
            # removed in the interim) -> fail rather than call the helper.
            job.state = JobState.failed
            job.reason = reason
            job.updated_at = datetime.now(UTC)
            session.add(job)
            session.commit()
            return
        try:
            files = helper.generate(job.case, inputs)
            artifact = helper.score(files)
        except GenerationError as exc:
            job.state = JobState.failed
            job.reason = str(exc)  # surface why it failed (no longer silent)
            job.updated_at = datetime.now(UTC)
            session.add(job)
            session.commit()
            return

        # Honour a cancel that landed mid-run: re-read state; if no longer
        # running, abort and persist no Generation (R9.4).
        session.refresh(job)
        if job.state is not JobState.running:
            return

        # Flip the prior latest for this (owner, paper, case) before inserting.
        prior = session.exec(
            select(Generation).where(
                Generation.owner_id == job.owner_id,
                Generation.paper_ref == job.paper_ref,
                Generation.case == job.case,
                Generation.is_latest == True,  # noqa: E712
            )
        ).all()
        for row in prior:
            row.is_latest = False
            session.add(row)
        session.flush()

        gen = Generation(
            owner_id=job.owner_id,
            paper_ref=job.paper_ref,
            case=job.case,
            files=[{"path": f.path, "content": f.content} for f in files],
            code_quality_score=artifact.score,
            code_quality_rationale=artifact.rationale,
            disclaimer=DISCLAIMER,
            is_latest=True,
        )
        session.add(gen)
        session.flush()

        job.state = JobState.succeeded
        job.generation_id = gen.id
        job.updated_at = datetime.now(UTC)
        session.add(job)
        session.commit()


def _job_read(job: GenerationJob) -> JobRead:
    """Report a running job past its deadline as failed (orphan bound)."""
    if job.state is JobState.running:
        deadline = job.updated_at + timedelta(seconds=get_settings().codegen_job_timeout_seconds)
        if datetime.now(UTC) > _aware(deadline):
            return JobRead(
                id=job.id, paper_ref=job.paper_ref, case=job.case,
                state=JobState.failed, reason=job.reason, generation_id=job.generation_id,
            )
    return JobRead.model_validate(job, from_attributes=True)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


# --- endpoints ----------------------------------------------------------------


@router.post("/jobs", response_model=JobRead)
def start_job(
    payload: JobCreate,
    bg: BackgroundTasks,
    response: Response,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> JobRead:
    # 1. Return the existing in-flight job for (user, paper, case) if any (R4.2).
    existing = session.exec(
        select(GenerationJob).where(
            GenerationJob.owner_id == user.id,
            GenerationJob.paper_ref == payload.paper_ref,
            GenerationJob.case == payload.case,
            GenerationJob.state.in_(_INFLIGHT),  # type: ignore[attr-defined]
        )
    ).first()
    if existing is not None:
        return _job_read(existing)

    # 2. Preconditions; unmet -> persist refused, helper never called (R4.3-R4.5).
    reason, _ = _precondition(session, payload.case, payload.paper_ref, user.id)
    if reason is not None:
        job = GenerationJob(
            owner_id=user.id, paper_ref=payload.paper_ref, case=payload.case,
            state=JobState.refused, reason=reason,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return JobRead.model_validate(job, from_attributes=True)

    # 3. Insert pending + schedule the worker (R4.1). The partial unique index is
    #    the source of truth for the race: on conflict, return the winner (R4.2).
    job = GenerationJob(owner_id=user.id, paper_ref=payload.paper_ref, case=payload.case)
    session.add(job)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        winner = session.exec(
            select(GenerationJob).where(
                GenerationJob.owner_id == user.id,
                GenerationJob.paper_ref == payload.paper_ref,
                GenerationJob.case == payload.case,
                GenerationJob.state.in_(_INFLIGHT),  # type: ignore[attr-defined]
            )
        ).first()
        if winner is not None:
            return _job_read(winner)
        raise
    session.refresh(job)
    bg.add_task(run_job, job.id)
    response.status_code = 202
    return JobRead.model_validate(job, from_attributes=True)


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(
    job_id: UUID,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> JobRead:
    job = session.get(GenerationJob, job_id)
    if job is None or job.owner_id != user.id:
        raise HTTPException(status_code=404, detail="not found")
    return _job_read(job)


@router.post("/jobs/{job_id}/cancel", response_model=JobRead)
def cancel_job(
    job_id: UUID,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> JobRead:
    # Owner-scoped (404 otherwise, R9.5). Cancel only an in-flight job; a
    # terminal job is returned unchanged (idempotent, R9.6).
    job = session.get(GenerationJob, job_id)
    if job is None or job.owner_id != user.id:
        raise HTTPException(status_code=404, detail="not found")
    if job.state in _INFLIGHT:
        job.state = JobState.cancelled
        job.updated_at = datetime.now(UTC)
        session.add(job)
        session.commit()
        session.refresh(job)
    return _job_read(job)


@router.get("/generations", response_model=list[GenerationRead])
def list_generations(
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> list[Generation]:
    return list(
        session.exec(
            select(Generation)
            .where(Generation.owner_id == user.id)
            .order_by(Generation.created_at.desc())  # type: ignore[attr-defined]
        ).all()
    )


@router.get("/generations/{gen_id}", response_model=GenerationRead)
def get_generation(
    gen_id: UUID,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> Generation:
    gen = session.get(Generation, gen_id)
    if gen is None or gen.owner_id != user.id:
        raise HTTPException(status_code=404, detail="not found")
    return gen


@router.get("/generations/{gen_id}/archive")
def download_archive(
    gen_id: UUID,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> Response:
    gen = session.get(Generation, gen_id)
    if gen is None or gen.owner_id != user.id:
        raise HTTPException(status_code=404, detail="not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DISCLAIMER.txt", gen.disclaimer)
        for f in gen.files:
            zf.writestr(str(f["path"]), str(f["content"]))
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="generation-{gen.id}.zip"'},
    )


@router.delete("/generations/{gen_id}", status_code=204)
def delete_generation(
    gen_id: UUID,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> None:
    gen = session.get(Generation, gen_id)
    if gen is None or gen.owner_id != user.id:
        raise HTTPException(status_code=404, detail="not found")
    session.delete(gen)
    session.commit()

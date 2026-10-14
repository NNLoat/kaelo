"""Worker + persistence properties (R5): run_job with a mocked helper.

run_job opens its own Session(engine), so these point codegen.engine at the test
container engine and manage rows directly (the rollback `session` fixture can't
see the worker's committed writes).
"""

import pytest
from sqlmodel import Session, delete, select

from app.core import codegen as helper
from app.core.codegen import ArtifactScore, Case, GenerationError, GenFile
from app.models.generation import Generation, GenerationJob, JobState
from app.models.paper import Paper
from app.models.reproducibility import ExperimentSetup
from app.models.user import User
from app.models.writer import PaperClaim, WriterManuscript, WriterSourceFile
from app.routers import codegen as api
from app.routers.writer import normalize_reference


@pytest.fixture
def db(engine):
    api.engine = engine
    yield engine
    with Session(engine) as s:
        s.exec(delete(GenerationJob))
        s.exec(delete(Generation))
        s.exec(delete(WriterSourceFile))
        s.exec(delete(WriterManuscript))
        s.exec(delete(PaperClaim))
        s.exec(delete(ExperimentSetup))
        s.exec(delete(Paper))
        s.exec(delete(User))
        s.commit()


def _user(engine) -> int:
    with Session(engine) as s:
        u = User(username="worker_u", password_hash="x")
        s.add(u)
        s.commit()
        return u.id


def _paper_with_setup(engine) -> str:
    """A paper with an available Experiment Setup, so the generate-case
    precondition passes. Returns the paper_ref (stringified paper id)."""
    with Session(engine) as s:
        p = Paper(title="T", abstract="A")
        s.add(p)
        s.commit()
        s.refresh(p)
        s.add(ExperimentSetup(paper_id=p.id, hyperparameters="lr=0.1", available=True))
        s.commit()
        return str(p.id)


def _job(engine, owner_id, *, case=Case.generate, paper_ref="1") -> GenerationJob:
    with Session(engine) as s:
        j = GenerationJob(owner_id=owner_id, paper_ref=paper_ref, case=case, state=JobState.pending)
        s.add(j)
        s.commit()
        s.refresh(j)
        return j


def _mock_ok(monkeypatch, score=0.8):
    monkeypatch.setattr(
        helper, "generate", lambda c, i: [GenFile("main.py", "x"), GenFile("README.md", "r")]
    )
    monkeypatch.setattr(helper, "score", lambda f: ArtifactScore(score, "fine"))


# Feature: code-generation, Property 3: A succeeded job yields exactly one latest, scored Generation
def test_succeeded_yields_one_latest_scored_generation(db, monkeypatch):
    uid = _user(db)
    job = _job(db, uid, paper_ref=_paper_with_setup(db))
    _mock_ok(monkeypatch, score=0.8)
    api.run_job(job.id)
    with Session(db) as s:
        done = s.get(GenerationJob, job.id)
        assert done.state is JobState.succeeded and done.generation_id is not None
        gens = s.exec(select(Generation).where(Generation.owner_id == uid)).all()
        assert len(gens) == 1
        g = gens[0]
        assert g.is_latest and g.code_quality_score == 0.8 and g.code_quality_rationale == "fine"
        assert g.disclaimer and g.id == done.generation_id


# Feature: code-generation, Property 4: Helper failure fails the job and persists no artifact
def test_helper_failure_fails_job_no_artifact(db, monkeypatch):
    uid = _user(db)
    job = _job(db, uid, paper_ref=_paper_with_setup(db))

    def _boom(c, i):
        raise GenerationError("boom")

    monkeypatch.setattr(helper, "generate", _boom)
    api.run_job(job.id)
    with Session(db) as s:
        assert s.get(GenerationJob, job.id).state is JobState.failed
        assert s.exec(select(Generation).where(Generation.owner_id == uid)).all() == []


# Feature: code-generation, Property 5: Generation never writes a Paper's Reproducibility Score
def test_generation_never_writes_paper_repro_score(db, monkeypatch):
    uid = _user(db)
    with Session(db) as s:
        p = Paper(title="T", abstract="A", reproducibility_score=0.42)
        s.add(p)
        s.commit()
        s.refresh(p)
        s.add(ExperimentSetup(paper_id=p.id, hyperparameters="lr=0.1", available=True))
        s.commit()
        pid = p.id
    job = _job(db, uid, paper_ref=str(pid))
    _mock_ok(monkeypatch)
    api.run_job(job.id)
    with Session(db) as s:
        assert s.get(Paper, pid).reproducibility_score == 0.42
        # The successful run did persist a Generation (so the invariant is real).
        assert s.exec(select(Generation).where(Generation.owner_id == uid)).first() is not None


# Feature: code-generation, R9.4: a job cancelled mid-run persists no artifact
def test_cancel_mid_run_persists_no_generation(db, monkeypatch):
    uid = _user(db)
    job = _job(db, uid, paper_ref=_paper_with_setup(db))

    # Simulate a cancel landing after the helper runs but before persistence:
    # flip the job to cancelled from a concurrent session during score().
    def _cancel_mid(f):
        with Session(db) as s:
            j = s.get(GenerationJob, job.id)
            j.state = JobState.cancelled
            s.add(j)
            s.commit()
        return ArtifactScore(0.8, "fine")

    monkeypatch.setattr(
        helper, "generate", lambda c, i: [GenFile("main.py", "x"), GenFile("README.md", "r")]
    )
    monkeypatch.setattr(helper, "score", _cancel_mid)
    api.run_job(job.id)
    with Session(db) as s:
        # The worker must honour the cancel: state stays cancelled, no Generation.
        assert s.get(GenerationJob, job.id).state is JobState.cancelled
        assert s.exec(select(Generation).where(Generation.owner_id == uid)).all() == []


# Feature: code-generation, Property 8: Re-run supersedes but retains the prior Generation
def test_rerun_supersedes_retains_prior(db, monkeypatch):
    uid = _user(db)
    _mock_ok(monkeypatch)
    ref = _paper_with_setup(db)
    j1 = _job(db, uid, paper_ref=ref)
    api.run_job(j1.id)
    j2 = _job(db, uid, paper_ref=ref)
    api.run_job(j2.id)
    with Session(db) as s:
        gens = s.exec(select(Generation).where(Generation.owner_id == uid)).all()
        assert len(gens) == 2
        latest = [g for g in gens if g.is_latest]
        assert len(latest) == 1


# Feature: code-generation, Property 10: Stored artifacts contain only derived text
def test_stored_files_are_derived_only(db, monkeypatch):
    uid = _user(db)
    job = _job(db, uid, paper_ref=_paper_with_setup(db))
    _mock_ok(monkeypatch)
    api.run_job(job.id)
    with Session(db) as s:
        g = s.exec(select(Generation).where(Generation.owner_id == uid)).first()
        assert g.files == [
            {"path": "main.py", "content": "x"},
            {"path": "README.md", "content": "r"},
        ]


# Feature: code-generation, R5.3: a writer job uses the persisted manuscript (+ source)
def test_writer_job_uses_uploaded_manuscript_and_source(db, monkeypatch):
    uid = _user(db)
    ref = "2401.09999"
    with Session(db) as s:
        claim = PaperClaim(
            owner_id=uid,
            paper_ref_normalized=normalize_reference(ref),
            paper_ref_original=ref,
        )
        s.add(claim)
        s.commit()
        s.refresh(claim)
        s.add(WriterManuscript(claim_id=claim.id, filename="paper.pdf", text="MS BODY"))
        s.add(WriterSourceFile(claim_id=claim.id, path="train.py", content="print('hi')"))
        s.commit()

    captured = {}

    def _capture_generate(case, inputs):
        captured["case"] = case
        captured["inputs"] = inputs
        return [GenFile("main.py", "x")]

    monkeypatch.setattr(helper, "generate", _capture_generate)
    monkeypatch.setattr(helper, "score", lambda f: ArtifactScore(0.9, "ok"))

    job = _job(db, uid, case=Case.writer, paper_ref=ref)
    api.run_job(job.id)

    # The job succeeded and persisted a Generation.
    with Session(db) as s:
        done = s.get(GenerationJob, job.id)
        assert done.state is JobState.succeeded and done.generation_id is not None
        gen = s.exec(select(Generation).where(Generation.owner_id == uid)).first()
        assert gen is not None and gen.case is Case.writer

    # The inputs handed to the helper reflect the upload (manuscript + source).
    assert captured["case"] is Case.writer
    inputs = captured["inputs"]
    assert inputs.manuscript_text == "MS BODY"
    assert inputs.uploaded_source is not None and "train.py" in inputs.uploaded_source


# Feature: code-generation, R4.5: a writer job with no manuscript never calls the helper
def test_writer_job_without_manuscript_does_not_run_helper(db, monkeypatch):
    uid = _user(db)
    ref = "2401.08888"
    # Claim exists but no manuscript -> run_job must fail without calling the helper.
    with Session(db) as s:
        s.add(
            PaperClaim(
                owner_id=uid,
                paper_ref_normalized=normalize_reference(ref),
                paper_ref_original=ref,
            )
        )
        s.commit()

    def _boom(case, inputs):  # pragma: no cover - must never run
        raise AssertionError("helper.generate must not be called when inputs are absent")

    monkeypatch.setattr(helper, "generate", _boom)

    job = _job(db, uid, case=Case.writer, paper_ref=ref)
    api.run_job(job.id)

    with Session(db) as s:
        assert s.get(GenerationJob, job.id).state is JobState.failed
        assert s.exec(select(Generation).where(Generation.owner_id == uid)).all() == []

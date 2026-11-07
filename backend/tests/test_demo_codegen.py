"""demo-mode: code generation, scoring and review are recorded and replayed.

All Bedrock calls are faked; replay uses a ChatBedrock that fails the test.
"""

import json
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlmodel import Session, delete

from app.core import codegen
from app.core.codegen import Case, GenerationInputs, ReviewInputs
from app.models.generation import Generation, GenerationJob, JobState
from app.models.user import User
from app.models.writer import PaperClaim, WriterManuscript, WriterSourceFile
from app.routers import codegen as api
from app.routers.writer import normalize_reference
from tests.demo_helpers import demo


class _Resp:
    def __init__(self, content):
        self.content = content


class _Fake:
    """A fake Bedrock chat that answers by prompt kind and counts live calls."""

    def __init__(self, files, score, review):
        self.calls = 0
        self._files, self._score, self._review = files, score, review

    def invoke(self, prompt):
        self.calls += 1
        if prompt.startswith("Review the paper"):
            return _Resp(self._review)
        if prompt.startswith("Rate the quality"):
            return _Resp(json.dumps({"score": self._score, "rationale": "ok"}))
        return _Resp(
            "\n".join(f"=== FILE: {p} ===\n{c}\n=== END ===" for p, c in self._files)
        )


def _boom(**_):
    raise AssertionError("replay must not build a live client")


def _fresh_client(monkeypatch, factory) -> None:
    monkeypatch.setattr(codegen, "ChatBedrock", factory)
    codegen._client.cache_clear()


_path = st.from_regex(r"[a-z]{1,8}\.py", fullmatch=True)
_body = st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc")), min_size=1, max_size=40)
_files = st.lists(st.tuples(_path, _body), min_size=1, max_size=3, unique_by=lambda f: f[0])


# Feature: demo-mode, Property 14: Recorded code generation replays identically
@settings(max_examples=100, deadline=None)
@given(
    files=_files,
    score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    review=st.text(alphabet=st.characters(blacklist_categories=("Cs",)), min_size=1).filter(
        lambda t: t.strip() != ""
    ),
    setup=_body,
)
def test_recorded_generation_replays_identically(files, score, review, setup) -> None:
    gen_in = GenerationInputs(experiment_setup=setup)
    rev_in = ReviewInputs(standard_key="baseline", criteria=[], metadata=setup)
    fake = _Fake(files, score, review)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "c.json"
        with pytest.MonkeyPatch.context() as mp:
            _fresh_client(mp, lambda **_: fake)
            with demo("record", path):
                live = (
                    codegen.generate(Case.generate, gen_in),
                    codegen.score(codegen.generate(Case.generate, gen_in)),
                    codegen.review(rev_in),
                )
            recorded_calls = fake.calls
            _fresh_client(mp, _boom)
            with demo("replay", path):
                replayed = (
                    codegen.generate(Case.generate, gen_in),
                    codegen.score(codegen.generate(Case.generate, gen_in)),
                    codegen.review(rev_in),
                )
            codegen._client.cache_clear()
        assert fake.calls == recorded_calls  # replay made no live call
    assert replayed == live


def test_mock_mode_still_bypasses_the_seam(tmp_path, monkeypatch) -> None:
    path = tmp_path / "c.json"
    s = codegen.get_settings().model_copy(update={"codegen_mock": True})
    monkeypatch.setattr(codegen, "get_settings", lambda: s)
    _fresh_client(monkeypatch, _boom)
    for mode in ("record", "replay"):
        with demo(mode, path):
            assert codegen.review(ReviewInputs("baseline", [])).content.startswith(
                "# Reproducibility Review (mock)"
            )
    assert not path.exists()
    codegen._client.cache_clear()


# --- The demo's writer review, end to end through the job worker -------------

_REF = "2610.09450"
_REVIEW = "# Reproducibility Review\n## Gaps and inconsistencies\n- no seed\n"


@pytest.fixture
def db(engine):
    api.engine = engine
    yield engine
    with Session(engine) as s:
        for model in (
            GenerationJob, Generation, WriterSourceFile, WriterManuscript, PaperClaim, User,
        ):
            s.exec(delete(model))
        s.commit()


def _run_review(engine, uid) -> Generation:
    with Session(engine) as s:
        job = GenerationJob(owner_id=uid, paper_ref=_REF, case=Case.review, state=JobState.pending)
        s.add(job)
        s.commit()
        s.refresh(job)
        job_id = job.id
    api.run_job(job_id)
    with Session(engine) as s:
        done = s.get(GenerationJob, job_id)
        assert done.state is JobState.succeeded, done.reason
        return s.get(Generation, done.generation_id)


def test_writer_review_replays_through_run_job(db, tmp_path, monkeypatch) -> None:
    with Session(db) as s:
        user = User(username="demo_w", password_hash="x")
        s.add(user)
        s.commit()
        s.refresh(user)
        claim = PaperClaim(
            owner_id=user.id,
            paper_ref_normalized=normalize_reference(_REF),
            paper_ref_original=_REF,
        )
        s.add(claim)
        s.commit()
        s.refresh(claim)
        s.add(WriterManuscript(claim_id=claim.id, filename="m.pdf", text="we train a model"))
        s.commit()
        uid = user.id

    path = tmp_path / "c.json"
    fake = _Fake([], 0.5, _REVIEW)
    _fresh_client(monkeypatch, lambda **_: fake)
    with demo("record", path):
        recorded = _run_review(db, uid)
    assert recorded.files[0]["content"] == _REVIEW.strip() and fake.calls == 1

    with Session(db) as s:  # same starting state as a fresh reset
        s.exec(delete(GenerationJob))
        s.exec(delete(Generation))
        s.commit()
    _fresh_client(monkeypatch, _boom)
    with demo("replay", path):
        replayed = _run_review(db, uid)
    codegen._client.cache_clear()
    assert replayed.files == recorded.files and fake.calls == 1
    entries = json.loads(path.read_text())["entries"]
    assert [v["label"][:13] for v in entries.values()] == ["Review the pa"]
    stored = json.dumps(entries)
    assert "we train a model" not in stored  # the prompt itself is never stored

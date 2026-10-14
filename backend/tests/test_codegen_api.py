"""Codegen_API endpoint tests (R4, R6): driven through TestClient.

The helper is never exercised here (jobs stay pending or are refused), so no
Bedrock mocking is needed. Owner scoping, auth, dedup, refusal, and delete are
asserted against the overridden test session.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.codegen import Case
from app.models.generation import Generation, GenerationJob, JobState
from app.models.paper import Paper
from app.models.reproducibility import ExperimentSetup
from app.routers import codegen as api


@pytest.fixture(autouse=True)
def _bg_engine(engine):
    """Point the background worker's engine at the test container, so a
    scheduled run_job (fired after the response) doesn't dial the real 'db'
    host. These tests assert only the synchronous response; the worker's own
    behavior is covered in test_codegen_worker_properties.py."""
    api.engine = engine
    yield


def _register_login(client: TestClient, username: str) -> None:
    creds = {"username": username, "password": "password123"}
    assert client.post("/api/auth/register", json=creds).status_code == 201
    assert client.post("/api/auth/login", json=creds).status_code == 200


def _start(client: TestClient, paper_ref: str, case: str):
    return client.post("/api/codegen/jobs", json={"paper_ref": paper_ref, "case": case})


def _gen(owner_id: int, *, paper_ref="1", files=None, disclaimer="d", is_latest=True) -> Generation:
    return Generation(
        owner_id=owner_id,
        paper_ref=paper_ref,
        case=Case.generate,
        files=files or [],
        code_quality_score=0.5,
        code_quality_rationale="x",
        disclaimer=disclaimer,
        is_latest=is_latest,
    )


def _paper_with_setup(session: Session, *, repo_url=None, available=True) -> int:
    p = Paper(title="T", abstract="A", repo_url=repo_url)
    session.add(p)
    session.commit()
    session.refresh(p)
    session.add(
        ExperimentSetup(paper_id=p.id, hyperparameters="lr=0.1", available=available)
    )
    session.commit()
    return p.id


# Feature: code-generation, Property 2: Unmet preconditions refuse without calling the helper
def test_generate_without_setup_refuses(client: TestClient):
    _register_login(client, "r2a")
    # paper_ref that doesn't resolve to a paper -> no setup -> refused.
    resp = client.post("/api/codegen/jobs", json={"paper_ref": "999", "case": "generate"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "refused" and body["reason"]


def test_align_without_repo_refuses(client: TestClient, session: Session):
    _register_login(client, "r2b")
    pid = _paper_with_setup(session, repo_url=None)
    resp = client.post("/api/codegen/jobs", json={"paper_ref": str(pid), "case": "align"})
    assert resp.json()["state"] == "refused"


def test_writer_without_upload_refuses(client: TestClient):
    _register_login(client, "r2c")
    resp = client.post("/api/codegen/jobs", json={"paper_ref": "1", "case": "writer"})
    assert resp.json()["state"] == "refused"


def test_generate_with_setup_schedules_pending(client: TestClient, session: Session):
    _register_login(client, "ok1")
    pid = _paper_with_setup(session)
    resp = client.post("/api/codegen/jobs", json={"paper_ref": str(pid), "case": "generate"})
    assert resp.status_code == 202
    assert resp.json()["state"] == "pending"


# Feature: code-generation, Property 1: At most one in-flight job per (user, paper, case)
def test_duplicate_start_returns_existing_inflight(client: TestClient, session: Session):
    _register_login(client, "dup1")
    pid = _paper_with_setup(session)
    first = _start(client, str(pid), "generate").json()
    # A second start while pending returns the same job, does not create another.
    second = _start(client, str(pid), "generate").json()
    assert first["id"] == second["id"]
    inflight = [
        j for j in session.exec(select(GenerationJob)).all()
        if j.state in (JobState.pending, JobState.running)
    ]
    assert len(inflight) == 1


# Feature: code-generation, Property 7: Unauthenticated requests never act
def test_unauthenticated_requests_rejected(client: TestClient):
    client.cookies.clear()
    assert _start(client, "1", "generate").status_code == 401
    assert client.get("/api/codegen/jobs/00000000-0000-0000-0000-000000000000").status_code == 401
    assert client.get("/api/codegen/generations").status_code == 401


# Feature: code-generation, Property 6: Owner scoping — cross-user access reads as absent
def test_cross_user_access_is_404(client: TestClient, session: Session):
    _register_login(client, "owner_a")
    pid = _paper_with_setup(session)
    job = _start(client, str(pid), "generate").json()
    # Switch to a different user.
    client.post("/api/auth/logout")
    client.cookies.clear()
    _register_login(client, "owner_b")
    assert client.get(f"/api/codegen/jobs/{job['id']}").status_code == 404


# Feature: code-generation, Property 9: Delete removes only the targeted Generation
def test_delete_removes_only_target(client: TestClient, session: Session):
    _register_login(client, "del1")
    # Create two generations directly for the logged-in user.
    me = client.get("/api/auth/me").json()
    g1 = _gen(me["id"], paper_ref="1", is_latest=False)
    g2 = _gen(me["id"], paper_ref="2", is_latest=True)
    session.add(g1)
    session.add(g2)
    session.commit()
    session.refresh(g1)
    session.refresh(g2)

    assert client.delete(f"/api/codegen/generations/{g1.id}").status_code == 204
    listed = client.get("/api/codegen/generations").json()
    ids = {g["id"] for g in listed}
    assert str(g2.id) in ids and str(g1.id) not in ids


def test_archive_contains_files_and_disclaimer(client: TestClient, session: Session):
    import io
    import zipfile

    _register_login(client, "arch1")
    me = client.get("/api/auth/me").json()
    g = _gen(
        me["id"],
        files=[{"path": "main.py", "content": "print(1)"}],
        disclaimer="UNVERIFIED",
    )
    session.add(g)
    session.commit()
    session.refresh(g)

    resp = client.get(f"/api/codegen/generations/{g.id}/archive")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = set(zf.namelist())
        assert names == {"DISCLAIMER.txt", "main.py"}
        assert zf.read("DISCLAIMER.txt").decode() == "UNVERIFIED"

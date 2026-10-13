"""Example/edge tests for the Auth_API endpoints."""

from fastapi.testclient import TestClient


def _creds(username: str = "alice", password: str = "password123") -> dict[str, str]:
    return {"username": username, "password": password}


def test_register_login_logout_happy_path(client: TestClient) -> None:
    reg = client.post("/api/auth/register", json=_creds())
    assert reg.status_code == 201
    assert reg.json() == {"id": reg.json()["id"], "username": "alice"}

    login = client.post("/api/auth/login", json=_creds())
    assert login.status_code == 200
    assert any(k.lower() == "set-cookie" for k in login.headers)

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "alice"

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200


def test_register_duplicate_username_conflicts(client: TestClient) -> None:
    assert client.post("/api/auth/register", json=_creds()).status_code == 201
    dup = client.post("/api/auth/register", json=_creds(password="different1"))
    assert dup.status_code == 409
    assert dup.json()["detail"] == "username unavailable"


def test_register_invalid_credentials_422(client: TestClient) -> None:
    resp = client.post("/api/auth/register", json={"username": "ab", "password": "short"})
    assert resp.status_code == 422
    fields = {v["field"] for v in resp.json()["detail"]}
    assert fields == {"username", "password"}


# R5.4: login with missing/empty field -> 422, no cookie.
def test_login_empty_field_422_no_cookie(client: TestClient) -> None:
    resp = client.post("/api/auth/login", json={"username": "", "password": ""})
    assert resp.status_code == 422
    assert not any(k.lower() == "set-cookie" for k in resp.headers)


# R6.5: logging out twice is idempotent — both unauthenticated after cookie clears.
def test_logout_twice_idempotent(client: TestClient) -> None:
    client.post("/api/auth/register", json=_creds())
    client.post("/api/auth/login", json=_creds())

    assert client.post("/api/auth/logout").status_code == 200
    client.cookies.clear()
    assert client.post("/api/auth/logout").status_code == 401


# R6.4: logout with no cookie -> 401, no state change.
def test_logout_without_session_401(client: TestClient) -> None:
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "not authenticated"


# R6.4: logout with a tampered cookie -> 401.
def test_logout_tampered_cookie_401(client: TestClient) -> None:
    client.cookies.set("session", "not-a-valid-token")
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 401


# Feature: accounts, Property 8: username uniqueness — at most one record per username
def test_username_uniqueness(client: TestClient) -> None:
    assert client.post("/api/auth/register", json=_creds()).status_code == 201
    # Every attempt after the first conflicts; the unique index is the guarantee.
    for _ in range(3):
        assert client.post("/api/auth/register", json=_creds()).status_code == 409
    # The original record is intact and still logs in.
    assert client.post("/api/auth/login", json=_creds()).status_code == 200

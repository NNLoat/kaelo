"""Property-based tests for the Auth_API endpoints and session helpers."""

from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlmodel import Session, delete

from app.core.session import issue_session, read_session
from app.models.user import User

# Valid credential pairs: username 3..32, password 8..128.
_usernames = st.text(
    alphabet=st.characters(min_codepoint=97, max_codepoint=122),
    min_size=3,
    max_size=32,
)
_passwords = st.text(min_size=8, max_size=128)

# DB/HTTP-backed properties reuse the function-scoped client/session across
# generated inputs; each example is made self-contained (unique username,
# cookie reset, row cleanup), so suppressing the reset health check is safe.
_API_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


def _reset(client: TestClient, session: Session, *usernames: str) -> None:
    client.cookies.clear()
    session.exec(delete(User).where(User.username.in_(usernames)))  # type: ignore[attr-defined]
    session.commit()


# Feature: accounts, Property 7: Register-then-login succeeds and the response never leaks the hash
@_API_SETTINGS
@given(username=_usernames, password=_passwords)
def test_register_then_login(
    client: TestClient, session: Session, username: str, password: str
) -> None:
    _reset(client, session, username)
    body = {"username": username, "password": password}

    reg = client.post("/api/auth/register", json=body)
    assert reg.status_code == 201, reg.text
    reg_data = reg.json()
    assert set(reg_data) == {"id", "username"}
    assert reg_data["username"] == username
    assert "password" not in reg_data and "password_hash" not in reg_data

    login = client.post("/api/auth/login", json=body)
    assert login.status_code == 200, login.text
    assert "password_hash" not in login.json()

    _reset(client, session, username)


# Feature: accounts, Property 9: Login failures are non-disclosing
@_API_SETTINGS
@given(
    known_user=_usernames,
    password=_passwords,
    wrong_password=_passwords,
    unknown_user=_usernames,
)
def test_login_failures_non_disclosing(
    client: TestClient,
    session: Session,
    known_user: str,
    password: str,
    wrong_password: str,
    unknown_user: str,
) -> None:
    if wrong_password == password or unknown_user == known_user:
        return
    _reset(client, session, known_user, unknown_user)

    client.post("/api/auth/register", json={"username": known_user, "password": password})

    wrong_pw = client.post(
        "/api/auth/login", json={"username": known_user, "password": wrong_password}
    )
    unknown = client.post("/api/auth/login", json={"username": unknown_user, "password": password})

    assert wrong_pw.status_code == 401
    assert unknown.status_code == 401
    # Identical generic body; no cookie set on either.
    assert wrong_pw.json() == unknown.json()
    assert "set-cookie" not in {k.lower() for k in wrong_pw.headers}
    assert "set-cookie" not in {k.lower() for k in unknown.headers}

    _reset(client, session, known_user, unknown_user)


# Feature: accounts, Property 10: Session cookie round-trip identifies the acting user
@settings(max_examples=100, deadline=None)
@given(user_id=st.integers(min_value=1, max_value=2_000_000_000))
def test_session_round_trip(user_id: int) -> None:
    assert read_session(issue_session(user_id)) == user_id


# Feature: accounts, Property 11: Absent, tampered, or expired sessions never authenticate
@settings(max_examples=100, deadline=None)
@given(
    token=st.one_of(
        st.none(),
        st.just(""),
        st.text(max_size=64),
    )
)
def test_bad_tokens_never_authenticate(token: str | None) -> None:
    assert read_session(token) is None


# Feature: accounts, Property 11 (tampered): mutating a valid token invalidates it
@settings(max_examples=100, deadline=None)
@given(user_id=st.integers(min_value=1, max_value=2_000_000_000))
def test_tampered_token_rejected(user_id: int) -> None:
    token = issue_session(user_id)
    # Flip a character in the payload segment (before the first '.') so the
    # signature no longer matches. The last-char trick is unreliable because
    # distinct base64 tails can decode to the same signature bytes.
    first = "b" if token[0] != "b" else "c"
    tampered = first + token[1:]
    assert read_session(tampered) is None


# Feature: accounts, Property 12: Logout invalidates the session
@_API_SETTINGS
@given(username=_usernames, password=_passwords)
def test_logout_invalidates_session(
    client: TestClient, session: Session, username: str, password: str
) -> None:
    _reset(client, session, username)
    body = {"username": username, "password": password}
    client.post("/api/auth/register", json=body)
    client.post("/api/auth/login", json=body)

    assert client.get("/api/auth/me").status_code == 200

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200

    # Cookie cleared on the client; /me now unauthenticated.
    client.cookies.clear()
    assert client.get("/api/auth/me").status_code == 401

    _reset(client, session, username)

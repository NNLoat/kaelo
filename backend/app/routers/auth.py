"""Auth_API: registration, login, logout, and current-user endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.security import (
    CredentialError,
    hash_password,
    validate_credentials,
    verify_password,
)
from app.core.session import (
    COOKIE_KWARGS,
    SESSION_COOKIE,
    current_user,
    issue_session,
)
from app.db.session import get_session
from app.models.user import User, UserRead

router = APIRouter(prefix="/api/auth", tags=["auth"])

_INVALID_LOGIN = "username or password is incorrect"


class Credentials(BaseModel):
    """Raw login/registration input.

    No length constraints here on purpose: the Credential_Helper is the single
    source of credential-format validation so the endpoint can return per-field
    {field, rule} violations (R4.4, R8.8).
    """

    username: str
    password: str


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: Credentials, session: Session = Depends(get_session)) -> User:
    violations = validate_credentials(payload.username, payload.password)
    if violations:
        raise HTTPException(
            status_code=422,
            detail=[{"field": v.field, "rule": v.rule} for v in violations],
        )
    try:
        password_hash = hash_password(payload.password)
    except CredentialError as exc:
        raise HTTPException(
            status_code=422,
            detail=[{"field": v.field, "rule": v.rule} for v in exc.violations],
        ) from exc

    user = User(username=payload.username, password_hash=password_hash)
    session.add(user)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="username unavailable") from exc
    session.refresh(user)
    return user


@router.post("/login", response_model=UserRead)
def login(
    payload: Credentials,
    response: Response,
    session: Session = Depends(get_session),
) -> User:
    # Missing/empty fields are a validation failure, not an auth failure (R5.4).
    if not payload.username or not payload.password:
        raise HTTPException(status_code=422, detail="username and password are required")

    user = session.exec(select(User).where(User.username == payload.username)).first()
    # Unknown user and wrong password take the same path and body (R5.2, R5.3).
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail=_INVALID_LOGIN)

    assert user.id is not None
    response.set_cookie(SESSION_COOKIE, issue_session(user.id), **COOKIE_KWARGS)
    return user


@router.post("/logout")
def logout(
    response: Response,
    user: User = Depends(current_user),
) -> dict[str, bool]:
    # current_user raises 401 for absent/expired/malformed/terminated sessions
    # (R6.4, R6.5), making logout idempotent. On a valid session, clear it.
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(current_user)) -> User:
    return user

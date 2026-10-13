"""Stateless signed session cookie helpers.

A session is a signed, timed token carrying the user id, stored in an
HTTP-only cookie. Signed with ``settings.session_secret`` via itsdangerous;
tampering invalidates the signature and expiry bounds the token's life.
"""

from fastapi import Cookie, Depends, HTTPException
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlmodel import Session

from app.core.config import get_settings
from app.db.session import get_session
from app.models.user import User

settings = get_settings()

SESSION_COOKIE = "session"
_SALT = "accounts-session"

_serializer = URLSafeTimedSerializer(settings.session_secret, salt=_SALT)

# Kwargs for Response.set_cookie when issuing the session cookie.
COOKIE_KWARGS = dict(
    httponly=True,
    samesite="lax",
    secure=settings.cookie_secure,
    max_age=settings.session_ttl_seconds,
    path="/",
)


def issue_session(user_id: int) -> str:
    """Return a signed token identifying ``user_id``."""
    return _serializer.dumps(user_id)


def read_session(token: str | None) -> int | None:
    """Return the user id from ``token``, or None if absent/bad/expired."""
    if not token:
        return None
    try:
        return _serializer.loads(token, max_age=settings.session_ttl_seconds)
    except (BadSignature, SignatureExpired):
        return None


def current_user(
    session: Session = Depends(get_session),
    token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> User:
    """Resolve the acting User from the session cookie, or raise 401."""
    user_id = read_session(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="not authenticated")
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="not authenticated")
    return user

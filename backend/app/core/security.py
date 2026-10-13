"""Credential_Helper: thin, framework-agnostic credential utilities.

Pure functions for password hashing, verification, and credential-format
validation. No FastAPI or SQLModel imports — the Auth_API calls these.
"""

from dataclasses import dataclass

from pwdlib import PasswordHash

USERNAME_MIN, USERNAME_MAX = 3, 32
PASSWORD_MIN, PASSWORD_MAX = 8, 128

# Hard bound on plaintext accepted by the hasher, independent of the stricter
# registration format rule (PASSWORD_MIN..PASSWORD_MAX).
_HASH_PLAINTEXT_MIN, _HASH_PLAINTEXT_MAX = 1, 128

_hasher = PasswordHash.recommended()  # Argon2


@dataclass(frozen=True)
class FieldViolation:
    field: str
    rule: str


class CredentialError(Exception):
    """Raised when a credential value is outside the allowed range."""

    def __init__(self, violations: list[FieldViolation]) -> None:
        self.violations = violations
        super().__init__("; ".join(f"{v.field}: {v.rule}" for v in violations))


def hash_password(plain: str) -> str:
    """Return an Argon2 hash of ``plain`` (1..128 chars).

    Raises CredentialError if the plaintext length is out of range (R8.2).
    """
    if not (_HASH_PLAINTEXT_MIN <= len(plain) <= _HASH_PLAINTEXT_MAX):
        raise CredentialError([FieldViolation("password", "length")])
    return _hasher.hash(plain)


def verify_password(plain: str, password_hash: str) -> bool:
    """Return True iff ``plain`` corresponds to ``password_hash``.

    An empty or malformed hash reports failure (returns False) rather than
    raising, so a corrupt stored value can never authenticate (R8.5).
    """
    if not password_hash:
        return False
    try:
        return _hasher.verify(plain, password_hash)
    except Exception:
        # pwdlib raises on a hash it cannot parse — treat as malformed.
        return False


def validate_credentials(username: str, password: str) -> list[FieldViolation]:
    """Return one FieldViolation per violated format rule, or [] if both pass.

    Rules: username 3..32 chars, password 8..128 chars (R8.7, R8.8).
    """
    violations: list[FieldViolation] = []
    if not (USERNAME_MIN <= len(username) <= USERNAME_MAX):
        violations.append(FieldViolation("username", "length"))
    if not (PASSWORD_MIN <= len(password) <= PASSWORD_MAX):
        violations.append(FieldViolation("password", "length"))
    return violations

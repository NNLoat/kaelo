"""Property-based tests for the Credential_Helper (core/security.py).

Argon2 is CPU-heavy, so password length is capped at 128 and max_examples=100.
"""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.core.security import (
    PASSWORD_MAX,
    PASSWORD_MIN,
    USERNAME_MAX,
    USERNAME_MIN,
    CredentialError,
    hash_password,
    validate_credentials,
    verify_password,
)

_PWD_SETTINGS = settings(max_examples=100, deadline=None)
# Plaintext the hasher accepts: 1..128 chars.
_plaintext = st.text(min_size=1, max_size=128)


# Feature: accounts, Property 1: Hash/verify round-trip, and hash is not the plaintext
@_PWD_SETTINGS
@given(password=_plaintext)
def test_hash_verify_round_trip(password: str) -> None:
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True


# Feature: accounts, Property 2: Hashing the same password twice yields distinct, verifiable hashes
@_PWD_SETTINGS
@given(password=_plaintext)
def test_same_password_distinct_hashes(password: str) -> None:
    h1 = hash_password(password)
    h2 = hash_password(password)
    assert h1 != h2
    assert verify_password(password, h1) is True
    assert verify_password(password, h2) is True


# Feature: accounts, Property 3: Verification rejects non-corresponding passwords
@_PWD_SETTINGS
@given(p1=_plaintext, p2=_plaintext)
def test_verify_rejects_non_corresponding(p1: str, p2: str) -> None:
    if p1 == p2:
        return
    assert verify_password(p2, hash_password(p1)) is False


# Feature: accounts, Property 4: Password-length validation on hashing
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
@given(
    bad=st.one_of(
        st.just(""),
        st.text(min_size=129, max_size=200),
    )
)
def test_hash_rejects_out_of_range(bad: str) -> None:
    try:
        hash_password(bad)
        raised = False
    except CredentialError:
        raised = True
    assert raised


# Feature: accounts, Property 5: Malformed hashes fail verification safely
@_PWD_SETTINGS
@given(password=_plaintext, bad_hash=st.text(max_size=64))
def test_malformed_hash_fails_safely(password: str, bad_hash: str) -> None:
    # A random/empty string is not a valid Argon2 hash; must return False, never raise.
    assert verify_password(password, bad_hash) is False


# Feature: accounts, Property 6: Credential validation reports exactly the violated rules
@settings(max_examples=100, deadline=None)
@given(
    username=st.text(max_size=40),
    password=st.text(max_size=140),
)
def test_validate_reports_exactly_violated_rules(username: str, password: str) -> None:
    violations = validate_credentials(username, password)
    fields = {v.field for v in violations}

    username_ok = USERNAME_MIN <= len(username) <= USERNAME_MAX
    password_ok = PASSWORD_MIN <= len(password) <= PASSWORD_MAX

    expected: set[str] = set()
    if not username_ok:
        expected.add("username")
    if not password_ok:
        expected.add("password")

    assert fields == expected

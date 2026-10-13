# Implementation Plan: accounts

## Overview

This plan implements the `accounts` authentication feature in dependency order
across the three mandated layers: Business Logic (`Credential_Helper`), Backend
persistence + `Auth_API`, and Frontend `Auth_UI`. Each layer builds on the
previous one and ends by wiring the pieces together, so there is no orphaned
code.

- **Backend verification gate:** after every backend task, `cd backend && uv run pytest`
  must pass (pytest + testcontainers against a throwaway `postgres:17`, run on
  the host per `backend/README.md`).
- **Schema:** the `users` table is created by an Alembic migration committed
  under `backend/alembic/versions/` and applied via `alembic upgrade head`
  (the container entrypoint) — **never** `create_all`.
- **New dependencies:** backend deps are added via `uv` (`pwdlib[argon2]`,
  `itsdangerous`, and `hypothesis` in the dev group); frontend deps (if any) via
  `pnpm`.
- **Frontend verification:** there is **no automated frontend test gate** — the
  team tests the UI manually. Frontend tasks are verified manually; do not
  invent a frontend test suite.
- Property-based tests use **Hypothesis** (min. 100 iterations each) and are
  tagged with a comment referencing the design property they validate.

## Tasks

- [x] 1. Business logic — `Credential_Helper` (`core/security.py`)
  - [x] 1.1 Add backend hashing dependency via uv
    - From `backend/`, run `uv add "pwdlib[argon2]"` so Argon2 hashing is
      available; confirm it lands in `pyproject.toml` and `uv.lock`.
    - _Requirements: 8.1, 4.5_

  - [x] 1.2 Implement `Credential_Helper` pure functions
    - Create `backend/app/core/security.py` with no FastAPI/SQLModel imports.
    - Define `USERNAME_MIN/MAX = 3/32`, `PASSWORD_MIN/MAX = 8/128`,
      `CredentialError`, and `FieldViolation` (`{field, rule}`).
    - `hash_password(plain)`: enforce 1..128 plaintext bound (raise
      `CredentialError` otherwise), else return an Argon2 hash via `pwdlib`.
    - `verify_password(plain, password_hash)`: return `True` iff they
      correspond; on empty/malformed hash, report malformed and return `False`
      (never raise, never return `True`).
    - `validate_credentials(username, password)`: return `[]` when both satisfy
      the format rules, else one `FieldViolation` per violated rule.
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

  - [x] 1.3 Add Hypothesis to the dev dependency group
    - From `backend/`, run `uv add --group dev hypothesis`; confirm it lands in
      `pyproject.toml` dev group and `uv.lock`.
    - _Requirements: 8.1_

  - [x]* 1.4 Write property test — hash/verify round-trip and hash ≠ plaintext
    - Create `backend/tests/test_security_properties.py`.
    - **Property 1: Hash/verify round-trip, and hash is not the plaintext**
    - **Validates: Requirements 8.1, 8.3, 4.5, 7.1**
    - Cap generated password length at 128; `max_examples=100` (Argon2 is
      CPU-heavy).

  - [x]* 1.5 Write property test — same password yields distinct, verifiable hashes
    - **Property 2: Hashing the same password twice yields distinct, verifiable hashes**
    - **Validates: Requirements 8.6**

  - [x]* 1.6 Write property test — verification rejects non-corresponding passwords
    - **Property 3: Verification rejects non-corresponding passwords**
    - **Validates: Requirements 8.4**

  - [x]* 1.7 Write property test — password-length validation on hashing
    - **Property 4: Password-length validation on hashing**
    - **Validates: Requirements 8.2**

  - [x]* 1.8 Write property test — malformed hashes fail verification safely
    - **Property 5: Malformed hashes fail verification safely**
    - **Validates: Requirements 8.5**

  - [x]* 1.9 Write property test — credential validation reports exactly the violated rules
    - **Property 6: Credential validation reports exactly the violated rules**
    - **Validates: Requirements 8.7, 8.8, 4.4**

- [x] 2. Checkpoint — Credential_Helper
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [x] 3. Data model, configuration, and migration (`User`, `Settings`)
  - [x] 3.1 Implement the `User` SQLModel
    - Create `backend/app/models/user.py` following the Base/Create/Read split
      from `item.py`: `UserBase` (username unique+indexed, 3..32),
      `User(table=True)` on `users` with `id` PK, `password_hash` (not null),
      `created_at` (UTC); `UserCreate` (plaintext `password` in, never stored);
      `UserRead` (`id` + `username`, **no** password/hash field).
    - _Requirements: 7.1, 7.4, 7.5, 4.2_

  - [x] 3.2 Extend `Settings` with session config
    - In `backend/app/core/config.py` add `session_secret: str` with **no
      default**, `session_ttl_seconds: int` (default 1 day), and
      `cookie_secure: bool = False`.
    - Document `SESSION_SECRET` in `.env.example` (placeholder only) and set a
      real value in `.env` (gitignored).
    - _Requirements: 7.6_

  - [x] 3.3 Generate and review the Alembic migration for the `users` table
    - Generate: `docker compose exec backend uv run alembic revision --autogenerate -m "create users table"`.
    - Review the draft so it creates `users` with the **unique index on
      `username`**; commit it under `backend/alembic/versions/`. The schema is
      applied by `alembic upgrade head` (entrypoint), **not** `create_all`.
    - _Requirements: 7.2, 7.4_

  - [x]* 3.4 Write migration smoke test
    - Extend `backend/tests/test_migrations.py` with an upgrade → downgrade →
      upgrade run asserting the `users` table and its unique `username` index
      exist after upgrade (single run, not PBT).
    - _Requirements: 7.2_

  - [x]* 3.5 Write config smoke test
    - Assert constructing `Settings` without `SESSION_SECRET` in the environment
      raises at startup (no committed default).
    - _Requirements: 7.6_

- [x] 4. Checkpoint — model, config, migration
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [x] 5. Session helpers and `Auth_API` router (backend)
  - [x] 5.1 Add the session-signing dependency via uv
    - From `backend/`, run `uv add itsdangerous` (skip only if already a pinned
      direct dep); confirm `pyproject.toml` and `uv.lock`.
    - _Requirements: 5.5, 5.6_

  - [x] 5.2 Implement session cookie helpers and `current_user` dependency
    - Create `backend/app/core/session.py` built on
      `itsdangerous.URLSafeTimedSerializer` keyed by `settings.session_secret`:
      `issue_session(user_id) -> str`, `read_session(token) -> int | None`
      (None on absent/bad/expired), `SESSION_COOKIE`, and `COOKIE_KWARGS`
      (`httponly`, `samesite="lax"`, `secure=cookie_secure`, `max_age=ttl`).
    - Implement a `current_user` dependency that reads the cookie, calls
      `read_session`, loads the `User`, or raises `401`.
    - _Requirements: 5.5, 5.6, 6.4_

  - [x] 5.3 Implement `routers/auth.py` endpoints
    - Create `backend/app/routers/auth.py` with `APIRouter(prefix="/api/auth")`
      using the existing `get_session` dependency and the `Credential_Helper`.
    - `POST /register`: validate via `validate_credentials` → `422` with
      per-field violations; hash via `hash_password`; insert `User`; catch
      `IntegrityError` → rollback + `409` "username unavailable"; success →
      `201 UserRead` (no hash).
    - `POST /login`: look up user, verify via `verify_password`; unknown user
      and wrong password take the same code path → identical generic `401`, no
      cookie; missing/empty field → `422`; success → `200 UserRead` +
      `Set-Cookie` session via `issue_session`.
    - `POST /logout`: valid session → `200` + clear cookie (`Max-Age=0`);
      absent/expired/malformed/already-terminated → `401` "not authenticated",
      no state change, idempotent.
    - `GET /me`: via `current_user` → `200 UserRead` or `401`.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 6.5, 7.3_

  - [x] 5.4 Register the auth router in `main.py`
    - Add `app.include_router(auth.router)` in `backend/app/main.py`; leave
      `/health` and `/api/items` routes untouched. This wires the backend
      together.
    - _Requirements: 4.1, 5.1, 6.1_

  - [x]* 5.5 Write property test — register-then-login succeeds and never leaks the hash
    - Create `backend/tests/test_auth_api_properties.py` driving endpoints via
      `TestClient` against the testcontainer DB.
    - **Property 7: Register-then-login succeeds and the response never leaks the hash**
    - **Validates: Requirements 4.1, 4.2, 5.1**

  - [x]* 5.6 Write property test — login failures are non-disclosing
    - **Property 9: Login failures are non-disclosing**
    - **Validates: Requirements 5.2, 5.3**

  - [x]* 5.7 Write property test — session cookie round-trip identifies the acting user
    - Test `issue_session`/`read_session` directly plus a cookie-carrying request.
    - **Property 10: Session cookie round-trip identifies the acting user**
    - **Validates: Requirements 5.5**

  - [x]* 5.8 Write property test — absent/tampered/expired sessions never authenticate
    - **Property 11: Absent, tampered, or expired sessions never authenticate**
    - **Validates: Requirements 5.6, 6.4**

  - [x]* 5.9 Write property test — logout invalidates the session
    - **Property 12: Logout invalidates the session**
    - **Validates: Requirements 6.1, 6.2, 6.3**

  - [x]* 5.10 Write example/edge tests for endpoints
    - Create `backend/tests/test_auth_api.py`: R5.4 login with missing/empty
      field → `422`, no cookie; R6.5 logout twice is idempotent; R6.4 logout
      with no/expired/tampered cookie → `401`, no state change; happy-path
      register/login/logout smoke.
    - _Requirements: 5.4, 6.4, 6.5_

  - [x]* 5.11 Write property test — username uniqueness (optional concurrency race)
    - **Property 8: Username uniqueness — at most one record per username**
    - Includes a targeted test issuing two near-simultaneous inserts of the same
      username and asserting exactly one row persists via the unique constraint.
    - **Validates: Requirements 4.3, 7.3, 7.4**

- [x] 6. Checkpoint — backend Auth_API
  - Ensure all tests pass (`cd backend && uv run pytest`), ask the user if
    questions arise.

- [x] 7. Frontend — `Auth_UI` (manual verification; no automated test gate)
  - [x] 7.1 Add any required frontend dependencies via pnpm
    - If the UI needs packages beyond the existing stack, add them from
      `frontend/` with `pnpm add <pkg>` (pinned). If none are needed, note that
      explicitly and skip. Do not switch package managers.
    - None needed: the existing React/TS/Tailwind + `fetch` stack covers the UI.
      Skipped.
    - _Requirements: 1.1, 2.1, 3.1_

  - [x] 7.2 Implement the typed API client `api/auth.ts`
    - Create `frontend/src/api/auth.ts` with `UserRead`/`FieldError` types and
      `register`, `login` (30s timeout), `logout` (10s timeout), and `me`.
    - Every call uses `credentials: "include"` and a per-request
      `AbortController` for timeouts.
    - _Requirements: 1.3, 1.4, 1.8, 2.3, 2.6, 3.3, 3.5, 5.5_

  - [x] 7.3 Implement `AuthProvider` + `useAuth`
    - Create `frontend/src/components/AuthProvider.tsx` holding
      `UserRead | null` and the active mode (`"reader" | "writer"`); call `me()`
      on mount to restore state; expose `register`, `login`, `logout`, `setMode`.
    - Reader mode active by default; exactly one mode at a time; when
      unauthenticated expose only login/register views (no modes/username/logout).
    - _Requirements: 3.2, 3.6, 5.5_

  - [x] 7.4 Implement `RegisterForm`
    - Create `frontend/src/components/RegisterForm.tsx`: username+password+submit;
      submit disabled while a field is empty or a request is in flight (progress
      indicator); client-side length gate (3..32 / 8..128); handle 201 success,
      409 conflict (retain username), 422 field errors, timeout/network error.
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

  - [x] 7.5 Implement `LoginForm`
    - Create `frontend/src/components/LoginForm.tsx`: username+password+enabled
      submit; "both required" when a field is empty; disable during request;
      handle success, 401 (retain username, clear password, generic message),
      timeout/unreachable retry message.
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 7.6 Implement `AuthBar` with logout and mode toggle
    - Create `frontend/src/components/AuthBar.tsx`: show signed-in username +
      logout control on every authenticated view; Reader/Writer mode toggle;
      disable logout during request; on success discard session + show login
      view; on failure/timeout keep authenticated state + re-enable + error.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 7.7 Wire Auth_UI into `App.tsx`
    - Wrap the app in `AuthProvider`; render login/register views when
      unauthenticated and `AuthBar` + authenticated content when authenticated.
      This integrates the frontend end-to-end.
    - _Requirements: 1.5, 2.4, 3.1, 3.4, 3.6_

- [ ] 8. Final checkpoint
  - Backend: ensure all tests pass (`cd backend && uv run pytest`). Frontend:
    manually verify register → login → authenticated state → mode toggle →
    logout flow in the browser. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; they
  are all tests. The core auth flow (unmarked tasks) is required.
- Task 5.11 (Property 8, including the concurrency race test) is optional — the
  unique DB constraint is the correctness guarantee; this test exercises it.
- Each task references specific requirements and/or design Property numbers for
  traceability.
- Backend gate: `cd backend && uv run pytest` (pytest + testcontainers, run on
  the host). Property tests use Hypothesis at ≥100 iterations.
- Schema is created by a committed Alembic migration under
  `backend/alembic/versions/` and applied via `alembic upgrade head` — never
  `create_all` (that exists only for test speed).
- Frontend has no automated test gate; verify UI manually.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "3.1", "3.2", "7.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "3.3", "5.1", "7.2"] },
    { "id": 2, "tasks": ["1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "3.4", "3.5", "5.2", "7.3"] },
    { "id": 3, "tasks": ["5.3", "7.4", "7.5", "7.6"] },
    { "id": 4, "tasks": ["5.4", "7.7"] },
    { "id": 5, "tasks": ["5.5", "5.6", "5.7", "5.8", "5.9", "5.10", "5.11"] }
  ]
}
```

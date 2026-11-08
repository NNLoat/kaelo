# Requirements Document

## Introduction

The `accounts` feature is the foundation authentication spec for the Open Science
Paper Engine. It provides lightweight username-and-password authentication:
registration, login, logout, and session handling. There is a single account
type — the `User` — and every `User` can use both `Reader` and `Writer` modes.
`Reader` and `Writer` are modes, not separate account types or roles, so there is
no role selection during registration.

This spec introduces the `User` table and establishes a stable, referenceable
account identity that later features (notably `writer-workspace`) depend on. The
work is deliberately layered into three concerns — Frontend (React UI), Backend
(FastAPI endpoints, persistence, and session handling), and Business Logic (thin
utility helpers for password hashing and credential validation) — so the layering
convention is set for subsequent specs.

Scope is limited to authentication and accounts. Paper search, scoring, code
generation, and writer uploads are out of scope and covered by later specs.

## Glossary

- **Account_System**: The authentication subsystem introduced by this spec,
  spanning the frontend UI, the backend endpoints, and the business-logic
  helpers that together implement registration, login, logout, and session
  handling.
- **Auth_API**: The backend (FastAPI) layer that exposes authentication
  endpoints (register, login, logout), persists the `User` record, and manages
  session state.
- **Auth_UI**: The frontend (React) layer that renders the registration form,
  login form, logout control, authenticated state, and error messages.
- **Credential_Helper**: The backend business-logic layer — utility-style
  functions for password hashing, password verification, and credential-format
  validation — that the `Auth_API` calls. It is a thin layer in this spec.
- **User**: An authenticated account identified by a unique username and a stored
  password hash. Every `User` can use both `Reader` and `Writer` modes.
- **Reader**: A mode in which a `User` finds, reads, and evaluates papers written
  by others. Available to every `User`; not a separate account type.
- **Writer**: A mode in which a `User` evaluates the reproducibility of a paper
  they claim as their own. Available to every `User`; not a separate account
  type.
- **Session**: The server-recognized authenticated state established at login and
  ended at logout, by which the `Auth_API` identifies the acting `User` on
  subsequent requests.
- **Password_Hash**: The stored one-way transformation of a `User` password,
  produced by the `Credential_Helper`. The plaintext password is never stored.

## Requirements

### Requirement 1: User Registration (Frontend)

**User Story:** As a prospective User, I want a registration form in the web UI,
so that I can create an account with a username and password.

#### Acceptance Criteria

1. WHEN a visitor opens the registration view, THE Auth_UI SHALL display a form with a username field, a password field, and a submit control.
2. WHILE the username field is empty or the password field is empty, THE Auth_UI SHALL keep the submit control disabled.
3. WHEN a visitor submits the registration form with a non-empty username of 3 to 32 characters and a non-empty password of 8 to 128 characters, THE Auth_UI SHALL send a registration request to the Auth_API containing the submitted username and password.
4. WHILE a registration request is in progress, THE Auth_UI SHALL disable the submit control and display a progress indicator until a response is received or the 30-second request timeout elapses.
5. WHEN the Auth_API reports that registration succeeded, THE Auth_UI SHALL display a confirmation message and present the authenticated state within 2 seconds of receiving the response.
6. IF the Auth_API reports that the username is already taken, THEN THE Auth_UI SHALL display a message stating that the username is unavailable, retain the submitted username value, and re-enable the submit control.
7. IF the Auth_API reports a validation error for the submitted credentials, THEN THE Auth_UI SHALL display the reported error message next to the form and re-enable the submit control.
8. IF no response is received from the Auth_API within the 30-second request timeout or the request fails due to a network or server error, THEN THE Auth_UI SHALL display an error message indicating that registration could not be completed, retain the submitted username value, and re-enable the submit control.

### Requirement 2: User Login (Frontend)

**User Story:** As a registered User, I want a login form in the web UI, so that I
can sign in to my account.

#### Acceptance Criteria

1. WHEN a visitor opens the login view, THE Auth_UI SHALL display a form with a username field, a password field, and an enabled submit control.
2. IF a visitor submits the login form while the username field or the password field is empty, THEN THE Auth_UI SHALL block the login request and display a message indicating that both username and password are required.
3. WHEN a visitor submits the login form with a non-empty username and a non-empty password, THE Auth_UI SHALL send a login request to the Auth_API and disable the submit control until a response is received or the request times out after 30 seconds.
4. WHEN the Auth_API reports that login succeeded, THE Auth_UI SHALL present the authenticated state for the signed-in User.
5. IF the Auth_API reports that the credentials are invalid, THEN THE Auth_UI SHALL re-enable the submit control, retain the entered username, clear the password field, and display a message stating that the username or password is incorrect.
6. IF the login request fails to receive a response within 30 seconds or the Auth_API is unreachable, THEN THE Auth_UI SHALL re-enable the submit control and display a message indicating that the login could not be completed and the visitor should retry.

### Requirement 3: Authenticated State and Logout (Frontend)

**User Story:** As a signed-in User, I want the UI to show that I am
authenticated and let me log out, so that I can confirm my session and end it
when finished.

#### Acceptance Criteria

1. WHILE a User is authenticated, THE Auth_UI SHALL display the signed-in User's username and a logout control, both remaining visible on every authenticated view.
2. WHILE a User is authenticated, THE Auth_UI SHALL make both Reader mode and Writer mode available to the signed-in User, with exactly one mode active at a time and Reader mode active by default on first entry to the authenticated state.
3. WHEN a signed-in User activates the logout control, THE Auth_UI SHALL send a logout request to the Auth_API and disable the logout control until the Auth_API responds or the request times out after 10 seconds.
4. WHEN the Auth_API reports that logout succeeded, THE Auth_UI SHALL discard the signed-in User's session state, present the unauthenticated state, and display the login view within 2 seconds of receiving the response.
5. IF the Auth_API reports that logout failed or no response is received within 10 seconds, THEN THE Auth_UI SHALL retain the authenticated state, re-enable the logout control, and display an error message indicating that logout did not complete.
6. WHILE no User is authenticated, THE Auth_UI SHALL present the unauthenticated state with access to the login view and the registration view, and SHALL NOT display Reader mode, Writer mode, the username, or the logout control.

### Requirement 4: Registration Endpoint (Backend)

**User Story:** As the frontend application, I want a registration endpoint, so
that I can create a new User from a submitted username and password.

#### Acceptance Criteria

1. WHEN the Auth_API receives a registration request with a username of 3 to 32 characters and a password of 8 to 128 characters that pass validation, THE Auth_API SHALL create a User record storing the username and the Password_Hash.
2. WHEN the Auth_API creates a User record, THE Auth_API SHALL return a success response identifying the created User by the User identifier and username, and SHALL NOT include the password or Password_Hash in the response.
3. IF the Auth_API receives a registration request with a username that already exists, THEN THE Auth_API SHALL reject the request with a conflict response, retain the existing User record unchanged, and SHALL NOT create a second User record.
4. IF the Auth_API receives a registration request whose credentials fail validation, THEN THE Auth_API SHALL reject the request with a validation-error response identifying each failing field and the rule it violated.
5. THE Auth_API SHALL delegate password hashing to the Credential_Helper and SHALL store only the Password_Hash, never the plaintext password.

### Requirement 5: Login and Session Establishment (Backend)

**User Story:** As the frontend application, I want a login endpoint that
establishes a session, so that subsequent requests are recognized as the
signed-in User.

#### Acceptance Criteria

1. WHEN the Auth_API receives a login request whose username matches an existing User and whose password verifies against the stored Password_Hash, THE Auth_API SHALL establish a Session for that User and return a success response identifying the authenticated User within 2 seconds.
2. IF the Auth_API receives a login request whose username does not match any User, THEN THE Auth_API SHALL reject the request with an authentication-failure response that does not disclose whether the username or the password was incorrect, and SHALL NOT establish a Session.
3. IF the Auth_API receives a login request whose password does not verify against the stored Password_Hash, THEN THE Auth_API SHALL reject the request with an authentication-failure response that does not disclose whether the username or the password was incorrect, and SHALL NOT establish a Session.
4. IF the Auth_API receives a login request in which the username or password field is missing or empty, THEN THE Auth_API SHALL reject the request with a validation-failure response indicating the required fields and SHALL NOT establish a Session.
5. WHEN the Auth_API receives a request carrying a valid Session, THE Auth_API SHALL identify the acting User from that Session.
6. IF the Auth_API receives a request carrying a Session that is absent, malformed, or expired, THEN THE Auth_API SHALL reject the request with an authentication-failure response and SHALL NOT identify an acting User.
7. THE Auth_API SHALL delegate password verification to the Credential_Helper.

### Requirement 6: Logout and Session Termination (Backend)

**User Story:** As the frontend application, I want a logout endpoint, so that a
User's session is terminated on request.

#### Acceptance Criteria

1. WHEN the Auth_API receives a logout request carrying a valid Session, THE Auth_API SHALL invalidate that Session and return a success response within 2 seconds.
2. WHEN the Auth_API invalidates a Session, THE Auth_API SHALL clear the Session credential held by the client such that it is no longer presented on subsequent requests.
3. WHEN the Auth_API receives a subsequent request carrying a Session that has been terminated, THE Auth_API SHALL treat the request as unauthenticated and return an unauthenticated response.
4. IF the Auth_API receives a logout request that carries no Session or a Session that is expired, malformed, or unrecognized, THEN THE Auth_API SHALL return an unauthenticated response and make no change to any existing Session.
5. IF the Auth_API receives a logout request for a Session that was already terminated, THEN THE Auth_API SHALL return an unauthenticated response without re-processing termination.

### Requirement 7: User Persistence and Schema (Backend)

**User Story:** As a developer of dependent features, I want the User persisted
with a stable identity through a committed migration, so that other features can
reference accounts reliably.

#### Acceptance Criteria

1. THE Auth_API SHALL persist each User with a unique User identifier, a unique username between 3 and 32 characters, and a Password_Hash, where the Password_Hash is never stored as plaintext.
2. THE Account_System SHALL introduce the User table through an Alembic migration committed under `backend/alembic/versions/`, and SHALL NOT create the User table through runtime schema generation (create_all).
3. WHEN a registration request supplies a username that already exists for a persisted User, THE Auth_API SHALL reject the request, retain the existing User record unchanged, and return a response indicating a username-conflict error.
4. WHEN two concurrent registration requests supply the same username, THE Account_System SHALL persist at most one User record for that username through a unique constraint on the username column.
5. THE Auth_API SHALL assign each User identifier at creation so that the identifier remains unchanged for the lifetime of the User record and is never reused for a different User.
6. IF a required database or secret configuration value is absent from the environment variables at startup, THEN THE Account_System SHALL fail to start and SHALL NOT read that value from committed source.

### Requirement 8: Credential Hashing and Validation (Business Logic)

**User Story:** As the backend, I want thin utility helpers for password hashing
and credential validation, so that authentication logic is reusable and
passwords are never stored in plaintext.

#### Acceptance Criteria

1. WHEN the Credential_Helper is given a plaintext password between 1 and 128 characters, THE Credential_Helper SHALL return a Password_Hash produced by a standard, well-known password-hashing algorithm, where the returned Password_Hash is not equal to the plaintext password.
2. IF the Credential_Helper is given a plaintext password that is empty or exceeds 128 characters, THEN THE Credential_Helper SHALL report a validation error indicating the password length is out of the allowed range and SHALL NOT return a Password_Hash.
3. WHEN the Credential_Helper is given a plaintext password and a Password_Hash that correspond, THE Credential_Helper SHALL return a boolean result indicating verification success.
4. IF the Credential_Helper is given a plaintext password and a Password_Hash that do not correspond, THEN THE Credential_Helper SHALL return a boolean result indicating verification failure.
5. IF the Credential_Helper is given a Password_Hash that is empty or not in the format produced by the password-hashing algorithm, THEN THE Credential_Helper SHALL report a validation error indicating the Password_Hash is malformed and SHALL report verification failure.
6. WHEN the Credential_Helper hashes the same plaintext password twice, THE Credential_Helper SHALL produce two distinct Password_Hash values that each verify successfully against that plaintext password.
7. WHEN the Credential_Helper is given a username and password to validate, THE Credential_Helper SHALL return a result indicating whether both satisfy the defined credential-format rules, where a username is 3 to 32 characters and a password is 8 to 128 characters.
8. IF the Credential_Helper is given credentials that violate one or more credential-format rules, THEN THE Credential_Helper SHALL return a result identifying each violated rule.

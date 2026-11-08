# Requirements Document

## Introduction

The `writer-workspace` feature lets a `User` acting in `Writer` mode claim a paper
they authored and upload the material needed to evaluate and generate against it:
the paper's **manuscript** (a PDF, from which text is extracted server-side) and
its **source code** (a zip or tarball upload, or a public Git URL). Unlike the
Reader/search side — which stores only an index and links (`docs/adr/0001`) —
**Writer-owned uploaded content is persisted** in Postgres, because the `User`
owns the work and consents to storing it. This is the single, deliberate
exception to the index-only rule, recorded in `docs/adr/0003`.

A `Writer` claims exactly one paper per `Paper_Claim`; a claim is the unit that
owns the uploaded manuscript and source. Once a claim carries an uploaded
manuscript, two existing features can run over it: `reproducibility-scoring`
(scores the claimed paper from the uploaded material) and `code-generation` case
3 — **Writer generation** — which generates code from the uploaded manuscript and,
when present, the uploaded source. The `code-generation` spec already refuses
Writer generation when "the requesting Writer has no uploaded manuscript for the
claimed paper" (its R4.5); this feature produces exactly that precondition: a
persisted manuscript tied to a `(User, Paper_Claim)`.

The work follows the layering convention set by `accounts`: Frontend (React UI),
Backend (FastAPI endpoints, persistence, PDF text extraction, archive/Git
ingestion), and Business Logic (thin, framework-agnostic helpers for extracting
manuscript text and for unpacking a source archive into stored files). It builds
on the `accounts` spec for `User` identity, the `current_user` dependency, and
the signed session cookie, and on the Writer-uploads carve-out (`docs/adr/0003`).

Two cross-cutting ingestion decisions were settled during grilling and recorded
as ADRs: upload ingestion runs **synchronously** inside the request rather than
as a background job (`docs/adr/0005`), and a public Git URL is fetched as an
**HTTP archive (codeload tarball)** and run through the same archive-unpack path
rather than cloned (`docs/adr/0006`). A further two refinements apply throughout:
only decodable **text** source files are stored (binary files in an upload are
skipped), and `Paper_Reference` de-duplication is **scoped to a single identifier
scheme** — the same paper reached via two different schemes (e.g. an arXiv URL and
a DOI) is two `Paper_Claim`s for now, since cross-identifier resolution needs the
`paper-search`/OpenAlex lookup that does not yet exist.

This spec **introduces** the `Paper_Claim`, `Writer_Manuscript`, and
`Writer_Source_File` tables and **produces** the persisted Writer uploads that
`reproducibility-scoring` and `code-generation` (case 3) consume. It does **not**
compute the `Reproducibility_Score`, extract the `Experiment_Setup`, or generate
code — those are owned by other specs and consume this feature's output.

Out of scope: computing the `Reproducibility_Score`; extracting the
`Experiment_Setup`; generating or aligning code (owned by `code-generation`);
Reader-side search and indexed-`Paper` storage (owned by `paper-search`);
cloning/storing a private Git repository or any repository behind auth; executing,
building, or running uploaded source; in-browser editing of uploaded files;
sharing a `Paper_Claim` or its uploads between `User`s; and verifying that the
claiming `User` is genuinely an author of the paper (claim is self-asserted).

## Glossary

- **Writer_Workspace**: The subsystem introduced by this spec, spanning the
  frontend UI, the backend endpoints and persistence, and the business-logic
  helpers that together implement claiming a paper and uploading, storing, and
  managing its manuscript and source.
- **Writer_API**: The backend (FastAPI) layer that exposes endpoints to create a
  `Paper_Claim`, upload a manuscript, upload source (archive or Git URL), list
  and read a `User`'s claims and their uploaded material, and delete a claim or
  its uploads; it owns persistence of all Writer-owned content.
- **Writer_UI**: The frontend (React) layer that renders the claim form, the
  manuscript upload control, the source upload control (file or Git URL), the
  list of the signed-in `User`'s claims, the per-claim material view, and the
  delete controls.
- **Extraction_Helper**: The backend business-logic layer that extracts plain
  text from an uploaded PDF manuscript and unpacks an uploaded source archive into
  a set of `(relative path, content)` files. Thin and framework-agnostic; takes
  bytes in and returns plain data out.
- **User**: An authenticated account (from the `accounts` spec). Every `User` can
  act in `Reader` or `Writer` mode. Identity and session come from `accounts`.
- **Writer**: The mode in which a `User` claims a paper as their own and uploads
  material to evaluate its reproducibility. Available to every `User`; not a
  separate account type.
- **Paper_Claim**: A `User`'s self-asserted claim to a specific paper, created by
  providing a paper reference (a link, a DOI, or an arXiv id). It is the owning
  record for that paper's uploaded manuscript and source. Owned by and visible
  only to the `User` who created it. A `User` holds at most one `Paper_Claim` per
  distinct paper reference.
- **Paper_Reference**: The identifier a `Writer` supplies to create a
  `Paper_Claim` — a URL, a DOI, or an arXiv id — normalized to a canonical form
  for de-duplication within a `User`'s claims.
- **Writer_Manuscript**: The persisted plain text extracted from a `Writer`'s
  uploaded PDF manuscript for a `Paper_Claim`, together with the original
  filename. At most one `Writer_Manuscript` exists per `Paper_Claim`; re-uploading
  replaces it. This is persisted Writer-owned content (`docs/adr/0003`).
- **Writer_Source_File**: One persisted file of a `Writer`'s uploaded source for a
  `Paper_Claim`, stored as a `(relative path, content)` row. A single source
  upload produces many `Writer_Source_File` rows. Only decodable **text** files
  are stored; binary files in an upload are skipped. This is persisted
  Writer-owned content (`docs/adr/0003`).
- **Source_Upload**: The act of providing source code for a `Paper_Claim`, either
  as an uploaded archive (zip or tarball) or as a public Git URL the backend
  fetches **as an HTTP archive (codeload tarball), not a clone** (`docs/adr/0006`).
  Either way the result is a set of `Writer_Source_File` text rows; the raw
  archive and the fetched repository tarball are not themselves retained.
- **Reproducibility_Score**: A paper-level rating produced by a separate feature
  that **consumes** a `Paper_Claim`'s uploaded material; never written by this
  spec.
- **Experiment_Setup**: The structured reproduction description produced by a
  separate feature from the manuscript/source; never produced by this spec.

## Requirements

### Requirement 1: Claim a Paper (Frontend)

**User Story:** As a Writer, I want to claim a paper by providing its reference,
so that I have a workspace that owns the material I upload for it.

#### Acceptance Criteria

1. WHILE a User is authenticated and in Writer mode, THE Writer_UI SHALL present a control to create a Paper_Claim with a single field for a Paper_Reference (a link, DOI, or arXiv id) and a submit control.
2. WHILE the Paper_Reference field is empty, THE Writer_UI SHALL keep the submit control disabled.
3. WHEN a Writer submits the claim form with a non-empty Paper_Reference, THE Writer_UI SHALL send a create-claim request to the Writer_API carrying the Paper_Reference and SHALL disable the submit control until a response is received or the 30-second request timeout elapses.
4. WHEN the Writer_API reports that a Paper_Claim was created or that a matching claim already exists for the Writer, THE Writer_UI SHALL present that claim's workspace view.
5. IF the Writer_API reports that the Paper_Reference is not a recognizable link, DOI, or arXiv id, THEN THE Writer_UI SHALL display the reported validation message, retain the entered value, and re-enable the submit control.
6. IF no response is received within the 30-second request timeout or the request fails due to a network or server error, THEN THE Writer_UI SHALL re-enable the submit control, retain the entered Paper_Reference, and display an error message indicating that the claim could not be created.

### Requirement 2: Upload a Manuscript (Frontend)

**User Story:** As a Writer, I want to upload my paper's PDF to a claim, so that
its text is stored for evaluation and generation.

#### Acceptance Criteria

1. WHILE a Writer is viewing one of their Paper_Claim workspaces, THE Writer_UI SHALL present a control to upload a manuscript that accepts a single PDF file.
2. IF the Writer selects a file whose type is not PDF or whose size exceeds the configured maximum, THEN THE Writer_UI SHALL reject the selection locally, display a message stating the accepted type and size limit, and SHALL NOT send an upload request.
3. WHEN a Writer uploads a PDF manuscript, THE Writer_UI SHALL send the file to the Writer_API for the current Paper_Claim and SHALL display a progress indicator until a response is received or the 60-second request timeout elapses.
4. WHEN the Writer_API reports that the manuscript was stored, THE Writer_UI SHALL indicate that the manuscript is present for the claim and SHALL present a control to replace it.
5. IF the Writer_API reports that text could not be extracted from the uploaded PDF, THEN THE Writer_UI SHALL display the reported reason, retain any previously stored manuscript unchanged, and re-enable the upload control.
6. IF no response is received within the 60-second request timeout or the request fails due to a network or server error, THEN THE Writer_UI SHALL display an error message indicating the upload did not complete, retain any previously stored manuscript unchanged, and re-enable the upload control.

### Requirement 3: Upload Source Code (Frontend)

**User Story:** As a Writer, I want to provide my paper's source as an archive or a
public Git URL, so that it is stored for evaluation and generation.

#### Acceptance Criteria

1. WHILE a Writer is viewing one of their Paper_Claim workspaces, THE Writer_UI SHALL present a source upload control offering both an archive upload (zip or tarball) and a public Git URL entry.
2. IF the Writer selects an archive whose type is not a supported archive or whose size exceeds the configured maximum, THEN THE Writer_UI SHALL reject the selection locally, display a message stating the accepted types and size limit, and SHALL NOT send an upload request.
3. WHEN a Writer submits an archive or a Git URL, THE Writer_UI SHALL send a Source_Upload request to the Writer_API for the current Paper_Claim and SHALL display a progress indicator until a response is received or the 120-second request timeout elapses.
4. WHEN the Writer_API reports that the source was stored, THE Writer_UI SHALL display the stored files as a read-only list of their relative paths, SHALL indicate how many files were skipped as binary when any were, and SHALL present a control to replace the source.
5. IF the Writer_API reports that the archive could not be unpacked or the Git URL could not be fetched, THEN THE Writer_UI SHALL display the reported reason, retain any previously stored source unchanged, and re-enable the source upload control.
6. IF no response is received within the 120-second request timeout or the request fails due to a network or server error, THEN THE Writer_UI SHALL display an error message indicating the upload did not complete, retain any previously stored source unchanged, and re-enable the source upload control.

### Requirement 4: Manage Claims and Uploaded Material (Frontend)

**User Story:** As a Writer, I want to see and delete my claims and their uploads,
so that I control my own persisted material.

#### Acceptance Criteria

1. WHILE a User is authenticated, THE Writer_UI SHALL display only the Paper_Claims owned by that User and SHALL NOT display any Paper_Claim owned by another User.
2. WHILE a Writer is viewing a Paper_Claim, THE Writer_UI SHALL indicate whether a manuscript is present and whether source is present for that claim.
3. WHEN a Writer activates the delete control for a manuscript or a source upload, THE Writer_UI SHALL send a delete request to the Writer_API and, on a success response, remove that material from the view while leaving the Paper_Claim and the other material in place.
4. WHEN a Writer activates the delete control for a Paper_Claim, THE Writer_UI SHALL send a delete request to the Writer_API and, on a success response, remove the claim and its uploaded material from the view.
5. IF a delete request fails or no response is received within the 30-second request timeout, THEN THE Writer_UI SHALL retain the affected item in the view and display an error message indicating that deletion did not complete.

### Requirement 5: Create and Normalize a Paper Claim (Backend)

**User Story:** As the frontend application, I want an endpoint that creates a
claim from a paper reference, so that a Writer has an owning record for uploads.

#### Acceptance Criteria

1. WHEN the Writer_API receives a create-claim request from an authenticated User carrying a Paper_Reference that is a recognizable link, DOI, or arXiv id, THE Writer_API SHALL normalize the Paper_Reference to a canonical form and create a Paper_Claim owned by that User, returning a response identifying the claim.
2. IF the Writer_API receives a create-claim request whose Paper_Reference is empty or is not a recognizable link, DOI, or arXiv id, THEN THE Writer_API SHALL reject the request with a validation-error response identifying the offending field and SHALL NOT create a Paper_Claim.
3. IF the Writer_API receives a create-claim request whose normalized Paper_Reference matches an existing Paper_Claim owned by the same User, THEN THE Writer_API SHALL NOT create a second Paper_Claim and SHALL return the existing claim. (De-duplication is scoped to a single identifier scheme: the same paper supplied under two different schemes — e.g. an arXiv URL and a DOI — normalizes to two distinct references and therefore two Paper_Claims; cross-identifier resolution is deferred to the `paper-search` feature.)
4. WHEN two Writers each claim the same Paper_Reference, THE Writer_API SHALL persist a separate Paper_Claim per User, each owned by and visible only to its creating User.
5. IF the Writer_API receives a create-claim request that carries no valid Session, THEN THE Writer_API SHALL reject the request with an unauthenticated response and SHALL NOT create a Paper_Claim.
6. THE Writer_API SHALL record each Paper_Claim with a stable identifier, its owning User, the normalized Paper_Reference, and the original supplied reference.

### Requirement 6: Store an Uploaded Manuscript (Backend)

**User Story:** As the frontend application, I want an endpoint that extracts and
stores manuscript text, so that the claimed paper's text is available to other
features.

#### Acceptance Criteria

1. WHEN the Writer_API receives a manuscript upload for a Paper_Claim owned by the authenticated User, THE Writer_API SHALL invoke the Extraction_Helper to extract plain text from the uploaded PDF and SHALL persist the extracted text and the original filename as the claim's Writer_Manuscript.
2. WHEN the Writer_API stores a Writer_Manuscript for a Paper_Claim that already has one, THE Writer_API SHALL replace the existing Writer_Manuscript so that at most one Writer_Manuscript exists per Paper_Claim.
3. IF the Writer_API receives a manuscript upload whose content is not a readable PDF or from which no text can be extracted (including a readable but text-empty PDF such as a pure scan), THEN THE Writer_API SHALL reject the request with an error identifying the reason, SHALL NOT persist a Writer_Manuscript, and SHALL leave any existing Writer_Manuscript unchanged.
4. IF the Writer_API receives a manuscript upload whose size exceeds the configured maximum, THEN THE Writer_API SHALL reject the request with an error indicating the size limit and SHALL NOT persist any content.
5. IF the Writer_API receives a manuscript upload for a Paper_Claim that is not owned by the authenticated User or does not exist, THEN THE Writer_API SHALL respond as though the claim does not exist for that User and SHALL NOT persist any content.
6. IF the Writer_API receives a manuscript upload that carries no valid Session, THEN THE Writer_API SHALL reject the request with an unauthenticated response and SHALL NOT persist any content.
7. THE Writer_API SHALL store only the extracted manuscript text and the original filename and SHALL NOT retain the raw uploaded PDF bytes after extraction completes.

### Requirement 7: Store Uploaded Source (Backend)

**User Story:** As the frontend application, I want an endpoint that unpacks and
stores source files from an archive or a public Git URL, so that the claimed
paper's source is available to other features.

#### Acceptance Criteria

1. WHEN the Writer_API receives a Source_Upload for a Paper_Claim owned by the authenticated User that supplies an archive, THE Writer_API SHALL invoke the Extraction_Helper to unpack the archive into a set of (relative path, content) files, SHALL store only the decodable text files and skip binary files, SHALL persist each stored file as a Writer_Source_File for the claim, and SHALL return both the stored relative paths and the relative paths it skipped as binary.
2. WHEN the Writer_API receives a Source_Upload for a Paper_Claim owned by the authenticated User that supplies a public Git URL, THE Writer_API SHALL fetch the repository as an HTTP archive (a codeload tarball; it SHALL NOT clone the repository), at the ref named in the supplied URL when it carries one and otherwise at the repository's default branch, unpack its files into a set of (relative path, content) files, store only the decodable text files, and SHALL persist each stored file as a Writer_Source_File for the claim.
3. WHEN the Writer_API stores source for a Paper_Claim that already has stored source, THE Writer_API SHALL replace the existing Writer_Source_File set with the newly uploaded set.
4. IF the Writer_API receives a Source_Upload whose archive cannot be unpacked, whose Git URL cannot be fetched as an archive (unreachable, an unsupported host that exposes no archive endpoint, or a repository requiring authentication), THEN THE Writer_API SHALL reject the request with an error identifying the reason and SHALL leave any existing Writer_Source_File set unchanged.
5. IF the Writer_API receives a Source_Upload whose archive size, unpacked total size, or file count exceeds the configured maximum, THEN THE Writer_API SHALL reject the request with an error indicating the exceeded limit and SHALL NOT persist any Writer_Source_File.
6. IF the Writer_API receives a Source_Upload for a Paper_Claim that is not owned by the authenticated User or does not exist, THEN THE Writer_API SHALL respond as though the claim does not exist for that User and SHALL NOT persist any content.
7. IF the Writer_API receives a Source_Upload that carries no valid Session, THEN THE Writer_API SHALL reject the request with an unauthenticated response and SHALL NOT persist any content.
8. THE Writer_API SHALL store only the unpacked (relative path, content) files and SHALL NOT retain the raw uploaded archive or a working copy of the fetched repository after unpacking completes.

### Requirement 8: Read and Delete Claims and Material (Backend)

**User Story:** As the frontend application, I want endpoints to read and remove a
Writer's claims and uploads, so that I can present and let the Writer control
their persisted material.

#### Acceptance Criteria

1. WHEN the Writer_API receives a list request from an authenticated User, THE Writer_API SHALL return only that User's Paper_Claims, each indicating whether a Writer_Manuscript and Writer_Source_File set are present.
2. WHEN the Writer_API receives a read request for a Paper_Claim owned by the authenticated User, THE Writer_API SHALL return the claim, whether a manuscript is present, and the relative paths of its Writer_Source_Files.
3. WHEN the Writer_API receives a delete request for a Writer_Manuscript or the Writer_Source_File set of a Paper_Claim owned by the authenticated User, THE Writer_API SHALL remove that material and leave the Paper_Claim and the other material unchanged.
4. WHEN the Writer_API receives a delete request for a Paper_Claim owned by the authenticated User, THE Writer_API SHALL remove the Paper_Claim together with its Writer_Manuscript and all its Writer_Source_Files.
5. IF the Writer_API receives a read or delete request for a Paper_Claim or its material that is not owned by the authenticated User or does not exist, THEN THE Writer_API SHALL respond as though the resource does not exist for that User and SHALL NOT disclose its contents or existence.
6. IF the Writer_API receives a read or delete request that carries no valid Session, THEN THE Writer_API SHALL reject the request with an unauthenticated response.

### Requirement 9: Writer Persistence and Schema (Backend)

**User Story:** As a developer of dependent features, I want Writer claims and
uploads persisted through committed migrations, so that `reproducibility-scoring`
and `code-generation` can rely on the uploaded material.

#### Acceptance Criteria

1. THE Writer_Workspace SHALL introduce the Paper_Claim, Writer_Manuscript, and Writer_Source_File tables through Alembic migrations committed under `backend/alembic/versions/`, and SHALL NOT create those tables through runtime schema generation (create_all).
2. THE Writer_API SHALL persist each Paper_Claim with a stable identifier, its owning User referencing the User table, the normalized Paper_Reference, and the original supplied reference.
3. THE Writer_Workspace SHALL enforce, through a unique constraint, at most one Paper_Claim per (User, normalized Paper_Reference).
4. THE Writer_Workspace SHALL enforce, through a constraint, at most one Writer_Manuscript per Paper_Claim.
5. THE Writer_API SHALL persist each Writer_Source_File as a (relative path, content) row associated with its Paper_Claim, with the relative path unique within that claim.
6. WHEN a Paper_Claim is deleted, THE Writer_Workspace SHALL remove its Writer_Manuscript and all its Writer_Source_Files so that no uploaded material is orphaned.
7. THE Writer_API SHALL persist Writer-owned uploaded content (manuscript text and source files) as the deliberate exception to the index-only rule (`docs/adr/0003`), and SHALL NOT persist Reader-side indexed-Paper full text or external repository contents under this feature.

### Requirement 10: Manuscript Extraction and Source Unpacking (Business Logic)

**User Story:** As the backend, I want thin, framework-agnostic helpers for PDF
text extraction and archive unpacking, so that ingestion logic is reusable and
testable without the web or database layers.

#### Acceptance Criteria

1. WHEN the Extraction_Helper is given the bytes of a readable PDF that contains a text layer, THE Extraction_Helper SHALL return the extracted non-empty plain text.
2. IF the Extraction_Helper is given bytes that are not a readable PDF, or from which no text can be extracted (including a readable but text-empty PDF such as a pure scan), THEN THE Extraction_Helper SHALL report an extraction error and SHALL NOT return text.
3. WHEN the Extraction_Helper is given the bytes of a supported archive (zip or tarball), THE Extraction_Helper SHALL return a set of (relative path, content) entries for its contained files.
4. WHEN the Extraction_Helper unpacks an archive, THE Extraction_Helper SHALL reject entries whose paths escape the archive root (for example via absolute paths or parent-directory traversal) and SHALL NOT return such entries.
5. IF the Extraction_Helper is given an archive that is not a supported type or cannot be unpacked, THEN THE Extraction_Helper SHALL report an unpack error and SHALL NOT return entries.
6. WHEN the Extraction_Helper unpacks an archive, THE Extraction_Helper SHALL exclude entries that are not regular files (such as directories, symlinks, or device entries) and SHALL exclude regular files whose content is not decodable as text, returning only decodable text regular-file entries.
7. IF the number of entries or the total unpacked size would exceed the configured maximum, THEN THE Extraction_Helper SHALL report a limit-exceeded error and SHALL NOT return a partial set.
8. THE Extraction_Helper SHALL NOT execute, build, run, or otherwise evaluate any uploaded or unpacked content.

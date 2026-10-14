"""Writer_API — paper claims + uploaded manuscript/source (R5-R9).

A ``PaperClaim`` is the owning record for a Writer's claimed paper; this router
creates and reads claims and (in tasks 5.2-5.4) manages their uploaded manuscript
and source. All reads/deletes are owner-scoped: a claim owned by another User (or
absent) is indistinguishable from not-found (404, R8.5). Normalization of the
supplied ``Paper_Reference`` lives here as a pure function so it is importable by
the property test (task 1.5) and deterministic/canonical (design Property 3).
"""

import re
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.extraction import (
    ExtractionError,
    LimitExceeded,
    UnpackError,
    extract_pdf_text,
    unpack_archive,
)
from app.core.session import current_user
from app.db.session import get_session
from app.models.user import User
from app.models.writer import (
    ClaimDetail,
    ClaimRead,
    ManuscriptRead,
    PaperClaim,
    SourceRead,
    WriterManuscript,
    WriterSourceFile,
)

router = APIRouter(prefix="/api/writer", tags=["writer"])

# arXiv ids: new scheme (2401.01234[v2]) or old scheme (math.GT/0309136).
_ARXIV_NEW = re.compile(r"\d{4}\.\d{4,5}(v\d+)?$")
_ARXIV_OLD = re.compile(r"[a-z-]+(\.[A-Z]{2})?/\d{7}(v\d+)?$", re.IGNORECASE)
_DOI = re.compile(r"10\.\d{4,9}/\S+$")
# Query params that carry no identity — tracking/referrer noise we drop (R5.1).
_TRACKING_PREFIXES = ("utm_", "ref", "fbclid", "gclid", "mc_")


def _canonical_arxiv(value: str) -> str | None:
    v = value.strip()
    if _ARXIV_NEW.fullmatch(v) or _ARXIV_OLD.fullmatch(v):
        return f"arxiv:{v.lower() if '/' in v else v}"
    return None


def _canonical_doi(value: str) -> str | None:
    v = value.strip()
    return f"doi:{v.lower()}" if _DOI.fullmatch(v) else None


def normalize_reference(raw: str) -> str | None:
    """Canonicalize a Paper_Reference, or return None if unrecognized (R5.1, R5.2).

    arXiv id -> ``arxiv:<id>``; DOI -> ``doi:<lowercased>``; an http(s) URL ->
    the URL with scheme/host lowercased and tracking query noise trimmed. The
    same reference up to case/scheme/query noise always maps to one string, and
    anything empty or unrecognized maps to ``None`` (design Property 3).
    """
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None

    # Bare arXiv id or DOI (no scheme).
    if (hit := _canonical_arxiv(value)) is not None:
        return hit
    if (hit := _canonical_doi(value)) is not None:
        return hit

    parts = urlsplit(value if "//" in value else f"//{value}", scheme="https")
    host = parts.hostname or ""
    path = parts.path

    # arxiv.org/abs/<id> (also /pdf/<id>).
    if host.endswith("arxiv.org"):
        m = re.search(r"/(?:abs|pdf)/(.+?)(?:\.pdf)?/?$", path)
        if m and (hit := _canonical_arxiv(m.group(1))) is not None:
            return hit
        return None

    # doi.org/<doi> (and dx.doi.org).
    if host.endswith("doi.org"):
        return _canonical_doi(path.lstrip("/"))

    # Generic http(s) URL: lowercase scheme+host, drop tracking query noise.
    # Require a scheme-bearing input or a dotted host so a bare phrase like
    # "not a ref" (which urlsplit would read as a host) is not accepted (R5.2).
    had_scheme = "//" in value
    if parts.scheme not in ("http", "https") or not host or any(c.isspace() for c in value):
        return None
    if not had_scheme and "." not in host:
        return None
    kept = [
        kv
        for kv in parts.query.split("&")
        if kv and not kv.split("=", 1)[0].lower().startswith(_TRACKING_PREFIXES)
    ]
    normalized_path = path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), host.lower(), normalized_path, "&".join(kept), ""))


class ClaimCreate(BaseModel):
    paper_ref: str


def _to_read(claim: PaperClaim, session: Session) -> ClaimRead:
    """Project a claim to ClaimRead, computing material presence (R8.1)."""
    has_manuscript = (
        session.exec(
            select(WriterManuscript.id).where(WriterManuscript.claim_id == claim.id)
        ).first()
        is not None
    )
    has_source = (
        session.exec(
            select(WriterSourceFile.id).where(WriterSourceFile.claim_id == claim.id)
        ).first()
        is not None
    )
    return ClaimRead(
        id=claim.id,
        paper_ref=claim.paper_ref_original,
        paper_ref_normalized=claim.paper_ref_normalized,
        has_manuscript=has_manuscript,
        has_source=has_source,
        created_at=claim.created_at,
    )


def _owned_claim(claim_id: UUID, user: User, session: Session) -> PaperClaim:
    """Fetch an owner-scoped claim or 404 — never disclosing another's claim (R8.5)."""
    claim = session.get(PaperClaim, claim_id)
    if claim is None or claim.owner_id != user.id:
        raise HTTPException(status_code=404, detail="not found")
    return claim


@router.post("/claims", response_model=ClaimRead)
def create_claim(
    payload: ClaimCreate,
    response: Response,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> ClaimRead:
    normalized = normalize_reference(payload.paper_ref)
    if normalized is None:
        # Empty/unrecognized reference: reject, create nothing (R5.2).
        raise HTTPException(
            status_code=422,
            detail=[{"field": "paper_ref", "rule": "not a recognizable link, DOI, or arXiv id"}],
        )

    claim = PaperClaim(
        owner_id=user.id,
        paper_ref_normalized=normalized,
        paper_ref_original=payload.paper_ref,
    )
    session.add(claim)
    try:
        session.commit()
    except IntegrityError:
        # The (owner_id, normalized) unique constraint closed the race: an
        # existing claim wins; return it unchanged with 200 (R5.3).
        session.rollback()
        existing = session.exec(
            select(PaperClaim).where(
                PaperClaim.owner_id == user.id,
                PaperClaim.paper_ref_normalized == normalized,
            )
        ).first()
        if existing is None:
            raise
        return _to_read(existing, session)
    session.refresh(claim)
    response.status_code = 201
    return _to_read(claim, session)


@router.get("/claims", response_model=list[ClaimRead])
def list_claims(
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> list[ClaimRead]:
    claims = session.exec(
        select(PaperClaim)
        .where(PaperClaim.owner_id == user.id)
        .order_by(PaperClaim.created_at.desc())  # type: ignore[attr-defined]
    ).all()
    return [_to_read(c, session) for c in claims]


@router.get("/claims/{claim_id}", response_model=ClaimDetail)
def get_claim(
    claim_id: UUID,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> ClaimDetail:
    claim = _owned_claim(claim_id, user, session)
    manuscript = session.exec(
        select(WriterManuscript).where(WriterManuscript.claim_id == claim.id)
    ).first()
    source_paths = list(
        session.exec(
            select(WriterSourceFile.path)
            .where(WriterSourceFile.claim_id == claim.id)
            .order_by(WriterSourceFile.path)  # type: ignore[arg-type]
        ).all()
    )
    base = _to_read(claim, session)
    return ClaimDetail(
        **base.model_dump(),
        manuscript=ManuscriptRead(filename=manuscript.filename) if manuscript else None,
        source_paths=source_paths,
    )


@router.post("/claims/{claim_id}/manuscript", response_model=ManuscriptRead)
def upload_manuscript(
    claim_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> ManuscriptRead:
    claim = _owned_claim(claim_id, user, session)

    # Read bounded by the cap: stop at one byte past the limit so an oversized
    # upload is rejected (413) before extraction, without buffering it all (R6.4).
    limit = get_settings().max_manuscript_bytes
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"manuscript exceeds {limit} bytes")

    try:
        text = extract_pdf_text(data)
    except ExtractionError as exc:
        # Leave any existing manuscript untouched (R6.3).
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Upsert: at most one manuscript per claim; replace the raw bytes with text (R6.2, R6.7).
    existing = session.exec(
        select(WriterManuscript).where(WriterManuscript.claim_id == claim.id)
    ).first()
    if existing is not None:
        existing.text = text
        existing.filename = file.filename or ""
        session.add(existing)
    else:
        session.add(WriterManuscript(claim_id=claim.id, filename=file.filename or "", text=text))
    session.commit()
    return ManuscriptRead(filename=file.filename or "")


@router.delete("/claims/{claim_id}/manuscript", status_code=204)
def delete_manuscript(
    claim_id: UUID,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> Response:
    claim = _owned_claim(claim_id, user, session)
    manuscript = session.exec(
        select(WriterManuscript).where(WriterManuscript.claim_id == claim.id)
    ).first()
    if manuscript is not None:
        session.delete(manuscript)
        session.commit()
    return Response(status_code=204)


# --- Public Git fetch (R7.2, docs/adr/0006): download a codeload tarball, never clone ---


def _codeload_url(git_url: str) -> str:
    """Resolve a public Git URL to its host's codeload tarball endpoint.

    Honors a ``/tree/<ref>`` or ``/releases/tag/<ref>`` ref embedded in the URL;
    otherwise fetches the default branch via ``HEAD`` (no extra API round-trip —
    both GitHub and GitLab resolve ``HEAD`` to the default branch). Raises
    ``ValueError`` for a host with no derivable archive endpoint (R7.4).
    """
    parts = urlsplit(git_url if "//" in git_url else f"//{git_url}", scheme="https")
    host = (parts.hostname or "").lower()
    segments = [s for s in parts.path.split("/") if s]
    if len(segments) < 2:
        raise ValueError("missing owner/repo")
    owner, repo = segments[0], segments[1]
    repo = repo[:-4] if repo.endswith(".git") else repo

    # Ref embedded in the URL: /tree/<ref> or /releases/tag/<ref>; else default (HEAD).
    ref = "HEAD"
    if "tree" in segments:
        i = segments.index("tree")
        if i + 1 < len(segments):
            ref = "/".join(segments[i + 1 :])
    elif "tag" in segments:
        i = segments.index("tag")
        if i + 1 < len(segments):
            ref = "/".join(segments[i + 1 :])

    if host == "github.com" or host.endswith(".github.com"):
        return f"https://codeload.github.com/{owner}/{repo}/tar.gz/{ref}"
    if host == "gitlab.com" or host.endswith(".gitlab.com"):
        return f"https://gitlab.com/{owner}/{repo}/-/archive/{ref}/{repo}-{ref}.tar.gz"
    raise ValueError(f"unsupported Git host: {host}")


def _fetch_git_tarball(git_url: str) -> bytes:
    """Download the repo's codeload tarball over HTTP (no clone).

    Raises ``HTTPException`` 422 for an unsupported host, an unreachable URL, or a
    4xx/auth response — a private repo's public archive endpoint simply fails,
    so it never fetches private content (R7.2, R7.4, ADR-0006).
    """
    try:
        url = _codeload_url(git_url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="repository could not be fetched") from exc
    timeout = get_settings().git_fetch_timeout_seconds
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=422, detail="repository could not be fetched") from exc
    if resp.status_code in (401, 403):
        raise HTTPException(status_code=422, detail="repository requires authentication")
    if resp.status_code >= 400:
        raise HTTPException(status_code=422, detail="repository could not be fetched")
    return resp.content


@router.post("/claims/{claim_id}/source", response_model=SourceRead)
def upload_source(
    claim_id: UUID,
    file: UploadFile | None = File(default=None),
    git_url: str | None = Form(default=None),
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> SourceRead:
    claim = _owned_claim(claim_id, user, session)

    if file is not None:
        # Bound the read by the archive cap: reject oversized before unpacking (R7.5).
        limit = get_settings().max_source_archive_bytes
        data = file.file.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(status_code=413, detail=f"archive exceeds {limit} bytes")
    elif git_url is not None:
        # Fetch the public codeload tarball; errors map to 422 (R7.2, R7.4).
        data = _fetch_git_tarball(git_url)
    else:
        raise HTTPException(status_code=422, detail="provide an archive file or a git_url")

    try:
        result = unpack_archive(data)
    except LimitExceeded as exc:
        # Prior source left unchanged (R7.5).
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except UnpackError as exc:
        # Prior source left unchanged (R7.4).
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Replace the whole set in one transaction: delete old, insert new (R7.3).
    for existing in session.exec(
        select(WriterSourceFile).where(WriterSourceFile.claim_id == claim.id)
    ).all():
        session.delete(existing)
    for sf in result.files:
        session.add(WriterSourceFile(claim_id=claim.id, path=sf.path, content=sf.content))
    session.commit()
    # Raw archive / tarball bytes are discarded here — only text rows persist (R7.8).
    return SourceRead(
        paths=sorted(sf.path for sf in result.files),
        skipped_paths=sorted(result.skipped),
    )


@router.delete("/claims/{claim_id}/source", status_code=204)
def delete_source(
    claim_id: UUID,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> Response:
    claim = _owned_claim(claim_id, user, session)
    rows = session.exec(select(WriterSourceFile).where(WriterSourceFile.claim_id == claim.id)).all()
    if rows:
        for row in rows:
            session.delete(row)
        session.commit()
    return Response(status_code=204)


@router.delete("/claims/{claim_id}", status_code=204)
def delete_claim(
    claim_id: UUID,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> Response:
    # Delete the owning claim row; the ON DELETE CASCADE child FKs
    # (writer_manuscripts.claim_id, writer_source_files.claim_id) remove its
    # manuscript and all source rows at the DB level — no orphans (R8.4, R9.6).
    # No ORM relationships are configured, so this emits a plain parent DELETE
    # and lets the DB cascade run (rather than nulling children).
    claim = _owned_claim(claim_id, user, session)
    session.delete(claim)
    session.commit()
    return Response(status_code=204)

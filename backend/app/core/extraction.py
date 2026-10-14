"""Extraction_Helper: derive storable text from Writer uploads.

Pure functions over bytes — no FastAPI/SQLModel imports — so the Writer_API can
call them and they stay unit-testable. Produces only the ADR-0003 carve-out:
derived manuscript text and unpacked ``(path, content)`` text source files. The
caller discards the raw PDF / archive bytes. Nothing here ever executes, builds,
or runs uploaded content (R10.8).
"""

import io
import tarfile
import zipfile
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from app.core.config import get_settings


@dataclass
class SourceFile:
    path: str
    content: str


@dataclass
class UnpackResult:
    """What ``unpack_archive`` kept and what it dropped as binary.

    ``files`` are the stored text entries; ``skipped`` are the relative paths of
    regular files dropped because they decoded as binary (R7.1, R10.6). Path-unsafe
    entries, directories, and symlinks are not reported — only binary skips.
    """

    files: list[SourceFile]
    skipped: list[str]


class ExtractionError(Exception):
    """A PDF could not be read, or carried no extractable text."""


class UnpackError(Exception):
    """An archive was unsupported or corrupt."""


class LimitExceeded(Exception):
    """An upload exceeded a count or size cap; no partial result is returned."""


def extract_pdf_text(data: bytes) -> str:
    """Return the non-empty text extracted from a PDF.

    Raises ``ExtractionError`` for a non-readable PDF or when no text can be
    extracted (e.g. a pure scan with no text layer) (R10.1, R10.2).
    """
    try:
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except (PyPdfError, ValueError, OSError) as exc:
        raise ExtractionError(f"unreadable PDF: {exc}") from exc
    if not text.strip():
        raise ExtractionError("no extractable text in PDF")
    return text


def _is_text(raw: bytes) -> str | None:
    """Return decoded UTF-8 text, or None if the bytes look binary.

    A null byte is a cheap binary sniff; a UTF-8 decode failure also means
    binary. Binary files are skipped from source storage (R10.4, ADR-0003).
    """
    if b"\x00" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _safe_path(name: str) -> bool:
    """Reject absolute paths and any ``..`` traversal (R10.6)."""
    if name.startswith("/") or name.startswith("\\"):
        return False
    parts = name.replace("\\", "/").split("/")
    return ".." not in parts


def unpack_archive(
    data: bytes,
    *,
    max_files: int | None = None,
    max_total_bytes: int | None = None,
) -> UnpackResult:
    """Unpack a zip or tar(.gz/.bz2/.xz) into safe, regular, text source files.

    Returns an ``UnpackResult`` whose ``files`` are the kept text entries and
    whose ``skipped`` are the relative paths of regular files dropped as binary
    (R7.1). Skips directories, symlinks, device entries; rejects path-escaping
    entries. Enforces the count and uncompressed-size caps **while reading** and
    raises ``LimitExceeded`` (never a partial set). Raises ``UnpackError`` on an
    unsupported or corrupt archive (R10.3-R10.7).
    """
    settings = get_settings()
    max_files = settings.max_source_files if max_files is None else max_files
    max_total_bytes = (
        settings.max_source_total_bytes if max_total_bytes is None else max_total_bytes
    )

    if zipfile.is_zipfile(io.BytesIO(data)):
        return _unpack_zip(data, max_files, max_total_bytes)
    try:
        tf = tarfile.open(fileobj=io.BytesIO(data))
    except tarfile.TarError as exc:
        raise UnpackError(f"unsupported or corrupt archive: {exc}") from exc
    with tf:
        return _unpack_tar(tf, max_files, max_total_bytes)


def _check_caps(count: int, total: int, max_files: int, max_total_bytes: int) -> None:
    if count > max_files:
        raise LimitExceeded(f"more than {max_files} files")
    if total > max_total_bytes:
        raise LimitExceeded(f"unpacked size over {max_total_bytes} bytes")


def _unpack_zip(data: bytes, max_files: int, max_total_bytes: int) -> UnpackResult:
    out: list[SourceFile] = []
    skipped: list[str] = []
    total = 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for info in zf.infolist():
                if info.is_dir() or not _safe_path(info.filename):
                    continue
                count = len(out) + 1
                total += info.file_size
                _check_caps(count, total, max_files, max_total_bytes)
                raw = zf.read(info)
                text = _is_text(raw)
                if text is None:
                    skipped.append(info.filename)
                    continue
                out.append(SourceFile(path=info.filename, content=text))
    except (zipfile.BadZipFile, OSError) as exc:
        raise UnpackError(f"corrupt zip: {exc}") from exc
    return UnpackResult(files=out, skipped=skipped)


def _unpack_tar(tf: tarfile.TarFile, max_files: int, max_total_bytes: int) -> UnpackResult:
    out: list[SourceFile] = []
    skipped: list[str] = []
    total = 0
    try:
        for member in tf.getmembers():
            # Only regular files; skip dirs, symlinks, devices, fifos (R10.4).
            if not member.isfile() or not _safe_path(member.name):
                continue
            count = len(out) + 1
            total += member.size
            _check_caps(count, total, max_files, max_total_bytes)
            fh = tf.extractfile(member)
            if fh is None:
                continue
            text = _is_text(fh.read())
            if text is None:
                skipped.append(member.name)
                continue
            out.append(SourceFile(path=member.name, content=text))
    except tarfile.TarError as exc:
        raise UnpackError(f"corrupt tar: {exc}") from exc
    return UnpackResult(files=out, skipped=skipped)

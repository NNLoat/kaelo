"""Extraction_Helper tests (core/extraction.py).

Pure, offline — no network, no code execution. PDF parsing is heavier, so the
PDF property test keeps max_examples modest.
"""

import io
import tarfile
import zipfile

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.extraction import (
    ExtractionError,
    LimitExceeded,
    SourceFile,
    UnpackError,
    extract_pdf_text,
    unpack_archive,
)

# A minimal valid PDF carrying the extractable text "Hello" (one page).
_VALID_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]"
    b"/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
    b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"5 0 obj<</Length 44>>stream\n"
    b"BT /F1 24 Tf 50 100 Td (Hello) Tj ET\n"
    b"endstream endobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000052 00000 n \n"
    b"0000000101 00000 n \n"
    b"0000000209 00000 n \n"
    b"0000000277 00000 n \n"
    b"trailer<</Size 6/Root 1 0 R>>\n"
    b"startxref\n371\n%%EOF\n"
)


def _zip_bytes(entries: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _tar_bytes(entries: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for name, content in entries.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tf.addfile(info, io.BytesIO(content))
    return buf.getvalue()


# Feature: writer-workspace, Property 4: PDF extraction round-trips readable PDFs,
# rejects the rest
def test_extract_pdf_round_trips_readable() -> None:
    assert "Hello" in extract_pdf_text(_VALID_PDF)


@settings(max_examples=50, deadline=None)
@given(junk=st.binary(max_size=64))
def test_extract_pdf_rejects_unreadable(junk: bytes) -> None:
    # Arbitrary bytes are not a readable, text-bearing PDF (R10.2).
    with pytest.raises(ExtractionError):
        extract_pdf_text(junk)


# Feature: writer-workspace, Property 5: archive unpack returns only safe, regular-file entries
def test_unpack_zip_skips_unsafe_and_binary() -> None:
    data = _zip_bytes(
        {
            "src/main.py": b"print('hi')",
            "../escape.py": b"bad",
            "/abs.py": b"bad",
            "dir/": b"",
            "bin.dat": b"\x00\x01\x02binary",
        }
    )
    out = unpack_archive(data)
    paths = {f.path for f in out.files}
    assert paths == {"src/main.py"}
    assert out.files == [SourceFile(path="src/main.py", content="print('hi')")]
    assert out.skipped == ["bin.dat"]


def test_unpack_tar_skips_unsafe_and_binary() -> None:
    data = _tar_bytes(
        {
            "src/main.py": b"print('hi')",
            "../escape.py": b"bad",
            "bin.dat": b"text\x00more",
        }
    )
    paths = {f.path for f in unpack_archive(data).files}
    assert paths == {"src/main.py"}


def test_unpack_rejects_corrupt_archive() -> None:
    with pytest.raises(UnpackError):
        unpack_archive(b"not an archive at all")


# Feature: writer-workspace, Property 6: unpack enforces caps without a partial result
def test_unpack_file_count_cap() -> None:
    data = _zip_bytes({f"f{i}.txt": b"x" for i in range(10)})
    with pytest.raises(LimitExceeded):
        unpack_archive(data, max_files=3)


def test_unpack_total_size_cap() -> None:
    data = _zip_bytes({"big.txt": b"x" * 1000})
    with pytest.raises(LimitExceeded):
        unpack_archive(data, max_total_bytes=100)


@settings(max_examples=100, deadline=None)
@given(n=st.integers(min_value=1, max_value=20), cap=st.integers(min_value=1, max_value=20))
def test_unpack_cap_never_partial(n: int, cap: int) -> None:
    data = _zip_bytes({f"f{i}.txt": b"x" for i in range(n)})
    if n > cap:
        with pytest.raises(LimitExceeded):
            unpack_archive(data, max_files=cap)
    else:
        assert len(unpack_archive(data, max_files=cap).files) == n

"""Common pre-merge record shape and the Source_Adapter contract.

Every adapter maps its Source's response into a ``SourceRecord`` — index
metadata and links only, never full text (R7.1, R7.6). A failure or timeout
raises ``SourceError`` so orchestration can record a failed Source (R7.5).
"""

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from app.models.paper import PaperDomain

_GITHUB_IN_TEXT = re.compile(r"github\.com/([\w.-]+)/([\w.-]+)", re.IGNORECASE)


def find_repo_url(text: str | None) -> str | None:
    """First GitHub repo linked in ``text``, canonicalized; None if there is none.

    Neither Source exposes a repository field, so the abstract is where authors
    put it. shortcut: GitHub only and first match wins, extend when GitLab etc. matter.
    """
    m = _GITHUB_IN_TEXT.search(text or "")
    if not m:
        return None
    repo = m.group(2).rstrip(".,;:)").removesuffix(".git")
    return f"https://github.com/{m.group(1)}/{repo}" if repo else None


class SourceError(Exception):
    """Raised when a Source_Adapter fails or times out."""


@dataclass
class SourceRecord:
    """A single paper record from one Source, before merge/de-dup."""

    source: str  # "openalex" | "arxiv"
    title: str
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None
    published_date: date | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    source_links: list[tuple[str, str]] = field(default_factory=list)  # (source, url)
    repo_url: str | None = None
    domain: PaperDomain = PaperDomain.unknown  # field domain at ingestion (R9.1-9.3)


class SourceAdapter(Protocol):
    name: str

    def fetch(self, query: str, *, limit: int, timeout: float) -> list[SourceRecord]: ...

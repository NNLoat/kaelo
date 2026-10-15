"""Merge_Dedup: collapse same-publication records into unified papers.

Pure functions over adapter output — no HTTP, no DB — so the heuristic is
unit-testable in isolation and tightenable later (R7.3).
"""

import re
from dataclasses import dataclass, field
from datetime import date

from app.models.paper import PaperDomain
from app.services.sources.base import SourceRecord


@dataclass
class MergedPaper:
    """One unified publication, recording every contributing Source (R7.4)."""

    title: str
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None
    published_date: date | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    repo_url: str | None = None
    sources: list[str] = field(default_factory=list)
    source_links: list[tuple[str, str]] = field(default_factory=list)
    domain: PaperDomain = PaperDomain.unknown


def _norm_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    d = doi.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d or None


def _norm_arxiv(arxiv_id: str | None) -> str | None:
    if not arxiv_id:
        return None
    a = arxiv_id.strip().lower()
    a = re.sub(r"^(arxiv:)?", "", a)
    a = re.sub(r"v\d+$", "", a)  # drop version suffix
    return a or None


def _norm_title(title: str | None) -> str:
    if not title:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def _norm_authors(authors: list[str]) -> set[str]:
    # Compare on last-name-ish tokens, lowercased, to tolerate formatting drift.
    out: set[str] = set()
    for a in authors:
        norm = re.sub(r"[^a-z\s]+", " ", a.lower()).split()
        if norm:
            out.add(norm[-1])
    return out


def same_publication(a: SourceRecord, b: SourceRecord) -> bool:
    """Heuristic (first iteration): same DOI, same arXiv id, or same title +
    overlapping authors."""
    da, db = _norm_doi(a.doi), _norm_doi(b.doi)
    if da and db:
        return da == db

    aa, ab = _norm_arxiv(a.arxiv_id), _norm_arxiv(b.arxiv_id)
    if aa and ab:
        return aa == ab

    ta, tb = _norm_title(a.title), _norm_title(b.title)
    if ta and ta == tb:
        return bool(_norm_authors(a.authors) & _norm_authors(b.authors))

    return False


def _richer(current: str | None, candidate: str | None) -> str | None:
    """Keep the richer (longer non-empty) scalar value."""
    if candidate and (not current or len(candidate) > len(current)):
        return candidate
    return current


def _fold(paper: MergedPaper, rec: SourceRecord) -> None:
    paper.title = _richer(paper.title, rec.title) or paper.title
    paper.abstract = _richer(paper.abstract, rec.abstract)
    paper.doi = paper.doi or rec.doi
    paper.arxiv_id = paper.arxiv_id or rec.arxiv_id
    paper.repo_url = paper.repo_url or rec.repo_url
    if rec.published_date and not paper.published_date:
        paper.published_date = rec.published_date
    if len(rec.authors) > len(paper.authors):
        paper.authors = list(rec.authors)
    if rec.source not in paper.sources:
        paper.sources.append(rec.source)
    if paper.domain is PaperDomain.unknown and rec.domain is not PaperDomain.unknown:
        paper.domain = rec.domain
    for link in rec.source_links:
        if link not in paper.source_links:
            paper.source_links.append(link)


def merge_dedup(record_groups: list[list[SourceRecord]]) -> list[MergedPaper]:
    """Collapse records that are the same publication into unified papers.

    Each ``MergedPaper`` records every contributing Source and keeps the richer
    non-empty value per field. Never fabricates text beyond adapter output.
    """
    merged: list[MergedPaper] = []
    for group in record_groups:
        for rec in group:
            match = next(
                (
                    m
                    for m in merged
                    if same_publication(
                        rec,
                        SourceRecord(
                            source=m.sources[0] if m.sources else "",
                            title=m.title,
                            authors=m.authors,
                            doi=m.doi,
                            arxiv_id=m.arxiv_id,
                        ),
                    )
                ),
                None,
            )
            if match is None:
                match = MergedPaper(title=rec.title)
                merged.append(match)
            _fold(match, rec)
    return merged

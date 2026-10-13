"""arXiv Source_Adapter.

Queries the arXiv Atom API, maps entries to ``SourceRecord``, and restricts to
CS categories (and Medicine-adjacent q-bio). Index metadata/links only (R7.1,
R7.2, R7.6). Any failure/timeout raises ``SourceError`` (R7.5).
"""

import re
from datetime import datetime
from xml.etree import ElementTree as ET

import httpx

from app.services.sources.base import SourceError, SourceRecord

_API_URL = "https://export.arxiv.org/api/query"
_ATOM = "{http://www.w3.org/2005/Atom}"
_ARXIV_NS = "{http://arxiv.org/schemas/atom}"

# CS categories plus q-bio (the Medicine-adjacent corpus arXiv carries).
_CATEGORIES = "cat:cs.* OR cat:q-bio.*"


class ArxivAdapter:
    name = "arxiv"

    def fetch(self, query: str, *, limit: int, timeout: float) -> list[SourceRecord]:
        params = {
            "search_query": f"all:{query} AND ({_CATEGORIES})",
            "start": "0",
            "max_results": str(limit),
        }
        try:
            resp = httpx.get(_API_URL, params=params, timeout=timeout)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
        except (httpx.HTTPError, ET.ParseError) as exc:
            raise SourceError(f"arxiv fetch failed: {exc}") from exc

        return [self._map(entry) for entry in root.findall(f"{_ATOM}entry")]

    def _map(self, entry: ET.Element) -> SourceRecord:
        title_el = entry.find(f"{_ATOM}title")
        title = (title_el.text or "").strip() if title_el is not None else ""

        summary_el = entry.find(f"{_ATOM}summary")
        abstract = (summary_el.text or "").strip() if summary_el is not None else None

        authors = [
            name.text.strip()
            for a in entry.findall(f"{_ATOM}author")
            if (name := a.find(f"{_ATOM}name")) is not None and name.text
        ]

        # The <id> is https://arxiv.org/abs/<id>; extract the bare id.
        id_el = entry.find(f"{_ATOM}id")
        raw_id = (id_el.text or "") if id_el is not None else ""
        arxiv_id = None
        m = re.search(r"arxiv\.org/abs/(.+)$", raw_id)
        if m:
            arxiv_id = m.group(1)

        doi_el = entry.find(f"{_ARXIV_NS}doi")
        doi = (doi_el.text or "").strip() if doi_el is not None and doi_el.text else None

        published_date = None
        pub_el = entry.find(f"{_ATOM}published")
        if pub_el is not None and pub_el.text:
            try:
                published_date = datetime.fromisoformat(pub_el.text.replace("Z", "+00:00")).date()
            except ValueError:
                published_date = None

        links: list[tuple[str, str]] = []
        if raw_id:
            links.append(("arxiv", raw_id))

        return SourceRecord(
            source="arxiv",
            title=title,
            authors=authors,
            abstract=abstract,
            published_date=published_date,
            doi=doi,
            arxiv_id=arxiv_id,
            source_links=links,
            repo_url=None,
        )

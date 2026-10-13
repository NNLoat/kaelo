"""OpenAlex Source_Adapter.

Queries the keyless OpenAlex REST API, maps works to ``SourceRecord``, and
restricts to the CS + Medicine domains. Index metadata/links only — never full
text (R7.1, R7.2, R7.6). Any failure/timeout raises ``SourceError`` (R7.5).
"""

from datetime import date

import httpx

from app.services.sources.base import SourceError, SourceRecord

_API_URL = "https://api.openalex.org/works"

# OpenAlex field ids: Computer Science = 17, Medicine = 27. Values of a single
# filter key are OR-ed with "|" (comma between keys would AND them). This scopes
# results to the two mandated domains (R7.2).
_FIELD_FILTER = "primary_topic.field.id:fields/17|fields/27"


class OpenAlexAdapter:
    name = "openalex"

    def fetch(self, query: str, *, limit: int, timeout: float) -> list[SourceRecord]:
        params = {
            "search": query,
            "filter": _FIELD_FILTER,
            "per-page": str(min(limit, 200)),
        }
        try:
            resp = httpx.get(_API_URL, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise SourceError(f"openalex fetch failed: {exc}") from exc

        return [self._map(work) for work in data.get("results", [])]

    def _map(self, work: dict) -> SourceRecord:
        doi = work.get("doi")
        if doi:
            doi = doi.replace("https://doi.org/", "")

        authors = [
            a["author"]["display_name"]
            for a in work.get("authorships", [])
            if a.get("author", {}).get("display_name")
        ]

        published = work.get("publication_date")
        published_date = None
        if published:
            try:
                published_date = date.fromisoformat(published)
            except ValueError:
                published_date = None

        links: list[tuple[str, str]] = []
        landing = (work.get("primary_location") or {}).get("landing_page_url")
        if landing:
            links.append(("openalex", landing))
        oa_url = (work.get("open_access") or {}).get("oa_url")
        if oa_url:
            links.append(("openalex", oa_url))

        return SourceRecord(
            source="openalex",
            title=work.get("display_name") or "",
            authors=authors,
            abstract=_reconstruct_abstract(work.get("abstract_inverted_index")),
            published_date=published_date,
            doi=doi,
            arxiv_id=None,
            source_links=links,
            repo_url=None,
        )


def _reconstruct_abstract(inverted: dict | None) -> str | None:
    """OpenAlex stores abstracts as an inverted index; rebuild the text."""
    if not inverted:
        return None
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted.items():
        for i in idxs:
            positions.append((i, word))
    if not positions:
        return None
    positions.sort()
    return " ".join(word for _, word in positions)

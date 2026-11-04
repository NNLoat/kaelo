"""Seam wrappers for demo-mode: sources, LLM, repo inspection.

Each wrapper is a thin adapter around ``cached()`` that supplies the key and the
codec; none changes a public signature. See specs/demo-mode/design.md.
"""

from collections.abc import Callable
from dataclasses import asdict
from datetime import date
from typing import Any

from langchain_core.messages import AIMessage

from app.models.paper import PaperDomain
from app.services.demo import cassette
from app.services.demo.cassette import cached
from app.services.repro.types import RepoSignals
from app.services.sources.base import SourceAdapter, SourceRecord


def _mode() -> str:
    return cassette.get_settings().demo_mode


# --- LLM seam -----------------------------------------------------------------


class CassetteChat:
    """Stands in for ``ChatBedrock``; builds the real client only on a live call."""

    def __init__(self, build: Callable[[], Any]):
        self._build = build
        self._real: Any = None

    def invoke(self, prompt: str) -> Any:
        from app.services.llm import _content_text  # local: llm imports this module

        def live() -> Any:
            if self._real is None:
                self._real = self._build()
            return self._real.invoke(prompt)

        return cached(
            "llm",
            {"prompt": prompt},
            live,
            encode=lambda resp: {"content": _content_text(resp)},
            decode=lambda d: AIMessage(content=d["content"]),
            label=prompt[:80],
            model=cassette.get_settings().bedrock_model_id,
        )


def wrap_chat(build: Callable[[], Any]) -> Any:
    """The real client when Demo_Mode is off; otherwise a Cassette-backed proxy."""
    return build() if _mode() == "off" else CassetteChat(build)


# --- Source seam --------------------------------------------------------------


def _encode_records(records: list[SourceRecord]) -> list[dict]:
    return [
        {
            **asdict(r),
            "authors": list(r.authors),
            "published_date": r.published_date.isoformat() if r.published_date else None,
            "domain": r.domain.value,
            "source_links": [list(link) for link in r.source_links],
        }
        for r in records
    ]


def _decode_records(data: list[dict]) -> list[SourceRecord]:
    return [
        SourceRecord(
            **{
                **d,
                "published_date": (
                    date.fromisoformat(d["published_date"]) if d["published_date"] else None
                ),
                "domain": PaperDomain(d["domain"]),
                "source_links": [tuple(link) for link in d["source_links"]],
            }
        )
        for d in data
    ]


class CassetteSource:
    def __init__(self, inner: SourceAdapter):
        self._inner = inner
        self.name = inner.name

    def fetch(self, query: str, *, limit: int, timeout: float) -> list[SourceRecord]:
        return cached(
            "source",
            {
                "source": self.name,
                "query": query,
                "limit": limit,
                "domains": list(cassette.get_settings().source_domains),
            },
            lambda: self._inner.fetch(query, limit=limit, timeout=timeout),
            encode=_encode_records,
            decode=_decode_records,
            label=f"{self.name}|{query}|{limit}",
        )


def wrap_source(adapter: SourceAdapter) -> SourceAdapter:
    return adapter if _mode() == "off" else CassetteSource(adapter)


# --- Repo seam ----------------------------------------------------------------


def cached_repo(repo_url: str, live: Callable[[], RepoSignals]) -> RepoSignals:
    return cached(
        "repo",
        {"repo_url": repo_url.strip()},
        live,
        encode=asdict,
        decode=lambda d: RepoSignals(**d),
        label=repo_url,
    )

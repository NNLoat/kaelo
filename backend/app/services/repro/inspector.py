"""Repo_Inspector — GitHub REST metadata inspection behind a RepoHost (R1).

Reads repository metadata only; never clones (R1.5). The GitHub token is read
from config, sent only in the ``Authorization`` header over HTTPS, and never
logged/persisted/returned/prompted (Security section, Property 12).
"""

import re
from datetime import UTC, datetime, timedelta
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.services.demo.seams import cached_repo
from app.services.repro.types import RepoSignals

_NOT_INSPECTABLE = RepoSignals(
    exists=False,
    has_readme=False,
    has_license=False,
    has_tests=False,
    recent_activity=False,
    inspectable=False,
    failed=False,
)

_GITHUB_URL = re.compile(r"https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+)")

# Filenames/dirs that signal a test suite via the repo's top-level tree.
_TEST_HINTS = ("test", "tests", "spec", "specs")


class RepoHost(Protocol):
    def inspect(self, repo_url: str, *, timeout: float) -> RepoSignals: ...


class GitHubRepoHost:
    """GitHub REST implementation (first iteration)."""

    def inspect(self, repo_url: str, *, timeout: float) -> RepoSignals:
        match = _GITHUB_URL.match(repo_url.strip())
        if not match:
            return _NOT_INSPECTABLE
        owner, repo = match.group(1), match.group(2).removesuffix(".git")

        settings = get_settings()
        base = settings.github_api_base.rstrip("/")
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"

        try:
            resp = httpx.get(f"{base}/repos/{owner}/{repo}", headers=headers, timeout=timeout)
        except httpx.HTTPError:
            return self._failed()

        if resp.status_code == 404:
            # Clean not-found: repo absent but inspection succeeded (R1.4).
            return RepoSignals(
                exists=False,
                has_readme=False,
                has_license=False,
                has_tests=False,
                recent_activity=False,
                inspectable=True,
                failed=False,
            )
        if resp.status_code != 200:
            return self._failed()

        meta = resp.json()
        recency_days = settings.repo_recency_days
        return RepoSignals(
            exists=True,
            has_readme=self._has_readme(base, owner, repo, headers, timeout),
            has_license=bool(meta.get("license")),
            has_tests=self._has_tests(base, owner, repo, headers, timeout),
            recent_activity=_is_recent(meta.get("pushed_at"), recency_days),
            inspectable=True,
            failed=False,
        )

    @staticmethod
    def _failed() -> RepoSignals:
        return RepoSignals(
            exists=False,
            has_readme=False,
            has_license=False,
            has_tests=False,
            recent_activity=False,
            inspectable=False,
            failed=True,
        )

    @staticmethod
    def _has_readme(base, owner, repo, headers, timeout) -> bool:
        url = f"{base}/repos/{owner}/{repo}/readme"
        try:
            resp = httpx.get(url, headers=headers, timeout=timeout)
        except httpx.HTTPError:
            return False
        return resp.status_code == 200

    @staticmethod
    def _has_tests(base, owner, repo, headers, timeout) -> bool:
        url = f"{base}/repos/{owner}/{repo}/contents"
        try:
            resp = httpx.get(url, headers=headers, timeout=timeout)
        except httpx.HTTPError:
            return False
        if resp.status_code != 200:
            return False
        entries = resp.json()
        if not isinstance(entries, list):
            return False
        for entry in entries:
            name = str(entry.get("name", "")).lower()
            if any(
                name == hint or name.startswith(f"{hint}_") or name.startswith(f"{hint}.")
                for hint in _TEST_HINTS
            ):
                return True
        return False


# Default host; swapped in tests with a fake.
_HOST: RepoHost = GitHubRepoHost()


def inspect_repo(repo_url: str | None) -> RepoSignals:
    """Inspect a repo URL; absent/malformed/non-GitHub -> not inspectable (R1.3)."""
    if not repo_url or not repo_url.strip():
        return _NOT_INSPECTABLE
    settings = get_settings()
    return cached_repo(
        repo_url,
        lambda: _HOST.inspect(repo_url, timeout=settings.repo_inspect_timeout_seconds),
    )


def _is_recent(pushed_at: str | None, recency_days: int) -> bool:
    if not pushed_at:
        return False
    try:
        pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return pushed >= datetime.now(UTC) - timedelta(days=recency_days)

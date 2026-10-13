"""Inspector outcomes + LLM failure handling. GitHub/LLM mocked, never real."""

import httpx
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.services.repro import extractor, inspector
from app.services.repro.explainer import explain
from app.services.repro.types import RepoSignals


def _route(responses):
    """Map an endpoint suffix -> (status, json) and fake httpx.get accordingly."""

    def fake_get(url, headers=None, timeout=None):
        for suffix, (status, body) in responses.items():
            if url.endswith(suffix):
                return httpx.Response(status, json=body, request=httpx.Request("GET", url))
        return httpx.Response(404, json={}, request=httpx.Request("GET", url))

    return fake_get


def test_clean_404_is_absent_but_inspectable(monkeypatch):
    monkeypatch.setattr(httpx, "get", _route({"/repos/o/r": (404, {})}))
    sig = inspector.GitHubRepoHost().inspect("https://github.com/o/r", timeout=1.0)
    assert sig.exists is False
    assert sig.inspectable is True
    assert sig.failed is False


def test_timeout_is_failed(monkeypatch):
    def boom(url, headers=None, timeout=None):
        raise httpx.TimeoutException("slow")

    monkeypatch.setattr(httpx, "get", boom)
    sig = inspector.GitHubRepoHost().inspect("https://github.com/o/r", timeout=0.01)
    assert sig.failed is True
    assert sig.inspectable is False


def test_rate_limit_403_is_failed(monkeypatch):
    monkeypatch.setattr(httpx, "get", _route({"/repos/o/r": (403, {})}))
    sig = inspector.GitHubRepoHost().inspect("https://github.com/o/r", timeout=1.0)
    assert sig.failed is True


@pytest.mark.parametrize("url", [None, "", "not a url", "https://gitlab.com/o/r"])
def test_non_github_or_malformed_not_inspectable(url):
    sig = inspector.inspect_repo(url)
    assert sig.inspectable is False
    assert sig.failed is False


def test_existing_repo_maps_signals(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "get",
        _route(
            {
                "/repos/o/r": (
                    200,
                    {"license": {"key": "mit"}, "pushed_at": "2099-01-01T00:00:00Z"},
                ),
                "/readme": (200, {}),
                "/contents": (200, [{"name": "tests"}, {"name": "src"}]),
            }
        ),
    )
    sig = inspector.GitHubRepoHost().inspect("https://github.com/o/r", timeout=1.0)
    assert sig.exists and sig.has_license and sig.has_readme and sig.has_tests
    assert sig.recent_activity is True


def test_extract_setup_raises_on_llm_error(monkeypatch):
    class Boom:
        def invoke(self, _):
            raise RuntimeError("llm down")

    monkeypatch.setattr(extractor, "_client", lambda: Boom())
    with pytest.raises(RuntimeError):
        extractor.extract_setup("t", "a")


def test_explain_propagates_so_seam_can_swallow(monkeypatch):
    class Boom:
        def invoke(self, _):
            raise RuntimeError("llm down")

    import app.services.repro.explainer as ex

    monkeypatch.setattr(ex, "_client", lambda: Boom())
    sig = RepoSignals(True, True, True, True, True, True, False)
    with pytest.raises(RuntimeError):
        explain(0.5, sig, 0.5)


# Property 9: Inspection distinguishes "signal absent" from "inspection failed".
# Validates: Requirements 1.1, 1.4
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.sampled_from([404, 403, 429, 500, 503]))
def test_absent_vs_failed_never_conflated(monkeypatch, status):
    monkeypatch.setattr(httpx, "get", _route({"/repos/o/r": (status, {})}))
    sig = inspector.GitHubRepoHost().inspect("https://github.com/o/r", timeout=1.0)
    if status == 404:
        assert sig.inspectable is True and sig.failed is False
    else:
        assert sig.failed is True


# Property 10: Non-GitHub or malformed repo URLs are not inspectable.
# Validates: Requirements 1.3
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.text(max_size=40))
def test_fuzz_urls_only_github_inspectable(monkeypatch, url):
    # Stub the network so a fuzzed valid github URL maps to a clean 404 (absent)
    # instead of hitting the real API.
    monkeypatch.setattr(httpx, "get", _route({}))
    sig = inspector.inspect_repo(url)
    if sig.inspectable:
        assert "github.com/" in url

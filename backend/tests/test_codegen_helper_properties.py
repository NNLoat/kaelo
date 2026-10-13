"""Generation_Helper / Scoring_Helper tests (core/codegen.py).

The LangChain chat model is mocked — never called for real.
"""

import json

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.core import codegen
from app.core.codegen import Case, GenerationError, GenerationInputs


class _FakeResp:
    def __init__(self, content):
        self.content = content


class _Client:
    def __init__(self, text):
        self._text = text

    def invoke(self, _):
        return _FakeResp(self._text)


_non_readme_path = st.text(min_size=1, max_size=20).filter(lambda s: "readme" not in s.lower())


# Feature: code-generation, Property 11: output always includes a README and defaults to Python
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    case=st.sampled_from(list(Case)),
    files=st.lists(
        st.fixed_dictionaries(
            {"path": _non_readme_path, "content": st.text(max_size=50)}
        ),
        max_size=4,
    ),
)
def test_generate_always_includes_readme(monkeypatch, case, files) -> None:
    monkeypatch.setattr(codegen, "_client", lambda: _Client(json.dumps({"files": files})))
    out = codegen.generate(case, GenerationInputs(experiment_setup="setup"))
    assert any(f.path.lower().startswith("readme") for f in out)


def test_generate_keeps_model_readme(monkeypatch) -> None:
    payload = {
        "files": [
            {"path": "README.md", "content": "# Mine"},
            {"path": "a.py", "content": "x=1"},
        ]
    }
    monkeypatch.setattr(codegen, "_client", lambda: _Client(json.dumps(payload)))
    out = codegen.generate(Case.generate, GenerationInputs(experiment_setup="s"))
    readmes = [f for f in out if f.path.lower().startswith("readme")]
    assert len(readmes) == 1 and readmes[0].content == "# Mine"


def test_generate_raises_on_llm_error(monkeypatch) -> None:
    class Boom:
        def invoke(self, _):
            raise RuntimeError("bedrock down")

    monkeypatch.setattr(codegen, "_client", lambda: Boom())
    with pytest.raises(GenerationError):
        codegen.generate(Case.generate, GenerationInputs(experiment_setup="s"))


def test_generate_raises_on_unparseable(monkeypatch) -> None:
    monkeypatch.setattr(codegen, "_client", lambda: _Client("not json at all"))
    with pytest.raises(GenerationError):
        codegen.generate(Case.generate, GenerationInputs(experiment_setup="s"))


def test_score_parses_and_clamps(monkeypatch) -> None:
    monkeypatch.setattr(
        codegen, "_client", lambda: _Client('{"score": 1.5, "rationale": "ok"}')
    )
    result = codegen.score([codegen.GenFile(path="a.py", content="x=1")])
    assert result.score == 1.0  # clamped
    assert result.rationale == "ok"


def test_score_raises_on_llm_error(monkeypatch) -> None:
    class Boom:
        def invoke(self, _):
            raise RuntimeError("bedrock down")

    monkeypatch.setattr(codegen, "_client", lambda: Boom())
    with pytest.raises(GenerationError):
        codegen.score([codegen.GenFile(path="a.py", content="x=1")])


def test_score_raises_on_unparseable(monkeypatch) -> None:
    monkeypatch.setattr(codegen, "_client", lambda: _Client("nope"))
    with pytest.raises(GenerationError):
        codegen.score([codegen.GenFile(path="a.py", content="x=1")])

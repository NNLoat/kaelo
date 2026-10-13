"""Generation_Helper and Scoring_Helper via Amazon Bedrock (LangChain).

The only Bedrock callers for code-generation (docs/adr/0002). No FastAPI or
SQLModel imports — the Codegen_API worker calls these. Generated code is never
executed or compiled (R7.5); ``score`` rates the files, it does not run them.

Output contract (R7.2, R7.3): ``generate`` always returns at least a README,
and defaults to Python when the material does not determine a language. On any
LLM or parse failure both helpers raise ``GenerationError`` (R7.5).
"""

import json
import re
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from langchain_aws import ChatBedrock

from app.core.config import get_settings


class Case(str, Enum):
    """Which generation flow produced the artifact (mirrors the frontend)."""

    generate = "generate"  # Reader, no repo: from scratch
    align = "align"  # Reader, has repo: align existing source
    writer = "writer"  # Writer: from uploaded manuscript + source


@dataclass
class GenFile:
    path: str
    content: str


@dataclass
class ArtifactScore:
    score: float  # 0..1
    rationale: str


@dataclass
class GenerationInputs:
    experiment_setup: str
    repo_link: str | None = None
    manuscript_text: str | None = None
    uploaded_source: str | None = None


class GenerationError(Exception):
    """Raised on any LLM call or response-parse failure."""


@lru_cache
def _client() -> ChatBedrock:
    settings = get_settings()
    return ChatBedrock(
        model=settings.bedrock_model_id,
        region_name=settings.aws_region,
    )


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def _content_text(resp) -> str:
    content = getattr(resp, "content", resp)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block) for block in content
        )
    return str(content)


_CASE_INSTRUCTION = {
    Case.generate: (
        "Generate runnable source code from scratch that implements the described "
        "experiment. Include a README overview."
    ),
    Case.align: (
        "Align and annotate the existing source so it matches the described "
        "experiment setup and README; do not rewrite it from scratch."
    ),
    Case.writer: (
        "Generate source code from the author's manuscript and uploaded source "
        "so the experiment is reproducible. Include a README overview."
    ),
}


def _build_prompt(case: Case, inputs: GenerationInputs) -> str:
    parts = [
        _CASE_INSTRUCTION[case],
        "Reply as JSON only: "
        '{"files": [{"path": "<relative path>", "content": "<file text>"}]}. '
        "Always include a README. If the material does not determine a language, "
        "write Python.",
        f"Experiment setup:\n{inputs.experiment_setup}",
    ]
    if inputs.repo_link:
        parts.append(f"Existing repository: {inputs.repo_link}")
    if inputs.manuscript_text:
        parts.append(f"Manuscript:\n{inputs.manuscript_text}")
    if inputs.uploaded_source:
        parts.append(f"Uploaded source:\n{inputs.uploaded_source}")
    return "\n\n".join(parts)


def _parse_files(text: str) -> list[GenFile]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise GenerationError(f"generation response not JSON: {text!r}")
    try:
        data = json.loads(match.group(0))
        raw = data["files"]
        files = [GenFile(path=str(f["path"]), content=str(f["content"])) for f in raw]
    except (ValueError, KeyError, TypeError) as exc:
        raise GenerationError(f"could not parse generation files: {exc}") from exc
    return files


def _ensure_readme(files: list[GenFile]) -> list[GenFile]:
    if any(re.match(r"readme", f.path, re.IGNORECASE) for f in files):
        return files
    return [GenFile(path="README.md", content="# Generated code\n"), *files]


def generate(case: Case, inputs: GenerationInputs) -> list[GenFile]:
    """Produce artifact files for the case. Never executes the output (R7.5).

    Guarantees a README is present (R7.2); the Python default (R7.3) is carried
    in the prompt. Raises ``GenerationError`` on LLM/parse failure.
    """
    try:
        resp = _client().invoke(_build_prompt(case, inputs))
    except Exception as exc:
        raise GenerationError(f"generation LLM call failed: {exc}") from exc
    files = _parse_files(_content_text(resp))
    return _ensure_readme(files)


def score(files: list[GenFile]) -> ArtifactScore:
    """Rate the generated files 0..1 with a short rationale (R7.4).

    Never executes the code. Raises ``GenerationError`` on LLM/parse failure.
    """
    listing = "\n\n".join(f"=== {f.path} ===\n{f.content}" for f in files)
    prompt = (
        "Rate the quality of this generated code on a 0.0-1.0 scale and give a "
        "one-sentence rationale. Do not run it. Reply as JSON: "
        '{"score": <float>, "rationale": "<text>"}.\n\n'
        f"{listing}"
    )
    try:
        resp = _client().invoke(prompt)
    except Exception as exc:
        raise GenerationError(f"scoring LLM call failed: {exc}") from exc
    text = _content_text(resp)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise GenerationError(f"scoring response not JSON: {text!r}")
    try:
        data = json.loads(match.group(0))
        return ArtifactScore(
            score=_clamp01(float(data["score"])),
            rationale=str(data["rationale"]),
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise GenerationError(f"could not parse score: {exc}") from exc

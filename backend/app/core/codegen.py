"""Generation_Helper and Scoring_Helper via Amazon Bedrock (LangChain).

The only Bedrock callers for code-generation (docs/adr/0002). No FastAPI or
SQLModel use of its own — the Codegen_API worker calls these; the only service
import is the demo-mode Cassette seam (ADR 0010). Generated code is never
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
from app.services.demo.seams import CassetteChat, wrap_chat


class Case(str, Enum):
    """Which generation flow produced the artifact (mirrors the frontend)."""

    generate = "generate"  # Reader, no repo: from scratch
    align = "align"  # Reader, has repo: align existing source
    writer = "writer"  # Writer: from uploaded manuscript + source
    review = "review"  # Review material against the Paper's standard (R12.2)


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


@dataclass
class CriterionFinding:
    """One Criterion of the Paper's Standard_Result, as plain data (R12.4).

    Mirrors the per-Criterion fields of reproducibility-scoring's
    ``CriterionResult`` without importing it, so this module keeps no dependency
    on the service layer.
    """

    id: str
    title: str
    status: str
    evidence_note: str


@dataclass
class ReviewInputs:
    """Role-aware material plus the Paper's Standard_Result for the Review case.

    Carries the same material the other cases use (per role: a Writer's
    ``manuscript_text`` + ``uploaded_source``; a Reader's index ``metadata`` +
    optional ``repo_link``) plus the Paper's ``Standard_Result`` — the selected
    standard key and its per-``Criterion`` statuses/notes read from
    reproducibility-scoring (R12.4). It adds **no** new access to full text
    beyond what the index-only rule already allows (R12.3).
    """

    standard_key: str
    criteria: list[CriterionFinding]
    repo_link: str | None = None
    metadata: str | None = None
    manuscript_text: str | None = None
    uploaded_source: str | None = None


class GenerationError(Exception):
    """Raised on any LLM call or response-parse failure."""


@lru_cache
def _client() -> ChatBedrock | CassetteChat:
    settings = get_settings()
    return wrap_chat(
        lambda: ChatBedrock(
            model=settings.bedrock_model_id,
            region_name=settings.aws_region,
            max_tokens=settings.codegen_max_tokens,
        )
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
        "Reply with one or more file blocks in exactly this format, nothing else:\n"
        "=== FILE: <relative path> ===\n"
        "<verbatim file contents>\n"
        "=== END ===\n"
        "Write the file contents literally — do NOT escape or wrap them as JSON. "
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


# Delimiter format avoids JSON-escaping the file body: generated code carries raw
# newlines/quotes that break json.loads inside a "content" string (R11).
_FILE_BLOCK = re.compile(
    r"===\s*FILE:\s*(?P<path>.+?)\s*===\n(?P<content>.*?)\n===\s*END\s*===",
    re.DOTALL,
)


def _parse_files(text: str) -> list[GenFile]:
    files = [
        GenFile(path=m.group("path").strip(), content=m.group("content"))
        for m in _FILE_BLOCK.finditer(text)
    ]
    if not files:
        raise GenerationError(f"no file blocks in generation response: {text!r}")
    return files


_MOCK_FILES = [
    GenFile(path="README.md", content="# Generated code (mock)\n\nDeterministic mock artifact.\n"),
    GenFile(path="main.py", content='print("mock generated code")\n'),
]


def _ensure_readme(files: list[GenFile]) -> list[GenFile]:
    if any(re.match(r"readme", f.path, re.IGNORECASE) for f in files):
        return files
    return [GenFile(path="README.md", content="# Generated code\n"), *files]


def generate(case: Case, inputs: GenerationInputs) -> list[GenFile]:
    """Produce artifact files for the case. Never executes the output (R7.5).

    Guarantees a README is present (R7.2); the Python default (R7.3) is carried
    in the prompt. Raises ``GenerationError`` on LLM/parse failure.
    """
    if get_settings().codegen_mock:
        return list(_MOCK_FILES)  # R10: no Bedrock call
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
    if get_settings().codegen_mock:
        return ArtifactScore(score=0.5, rationale="Mock score (codegen_mock enabled).")  # R10
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


_MOCK_REVIEW = GenFile(
    path="REVIEW.md",
    content=(
        "# Reproducibility Review (mock)\n\n"
        "Deterministic mock report. Unverified; nothing was executed.\n\n"
        "## Gaps and inconsistencies\n\n"
        "- (mock) No gaps identified against the standard.\n\n"
        "## Recommended improvements\n\n"
        "- (mock) No improvements recommended.\n"
    ),
)


def _build_review_prompt(inputs: ReviewInputs) -> str:
    criteria_lines = (
        "\n".join(
            f"- [{c.status}] {c.id} — {c.title}: {c.evidence_note}" for c in inputs.criteria
        )
        or "- (no per-criterion results available)"
    )
    parts = [
        "Review the paper's manuscript and existing code against its applicable "
        "reproducibility standard. Produce findings only — do NOT write any code, "
        "do NOT compute or report a numeric score, and do NOT run or compile "
        "anything. List the gaps and inconsistencies that affect reproducibility, "
        "then recommend specific improvements to the manuscript and code.",
        "Reply with a single Markdown document, nothing else. Use these sections:\n"
        "# Reproducibility Review\n"
        "## Gaps and inconsistencies\n"
        "## Recommended improvements",
        f"Applicable reproducibility standard: {inputs.standard_key}",
        f"Per-criterion results from the standard:\n{criteria_lines}",
    ]
    if inputs.metadata:
        parts.append(f"Paper index metadata:\n{inputs.metadata}")
    if inputs.repo_link:
        parts.append(f"Existing repository: {inputs.repo_link}")
    if inputs.manuscript_text:
        parts.append(f"Manuscript:\n{inputs.manuscript_text}")
    if inputs.uploaded_source:
        parts.append(f"Uploaded source:\n{inputs.uploaded_source}")
    return "\n\n".join(parts)


def review(inputs: ReviewInputs) -> GenFile:
    """Review material against the Paper's standard; return a single ``REVIEW.md``.

    Builds a review prompt from the role-aware material (a Writer's manuscript +
    uploaded source; a Reader's index metadata + optional repo link) grounded in
    the Paper's ``Standard_Result`` (R12.3, R12.4), calls Bedrock via LangChain,
    and returns one ``REVIEW.md`` ``GenFile`` listing gaps/inconsistencies against
    the standard plus recommended improvements (R12.6).

    Produces findings only — never code, never an ``Artifact_Code_Quality_Score``
    (R12.8); never executes anything (R7.5). Honors ``codegen_mock`` with a fixed
    report (R10). Raises ``GenerationError`` on any LLM failure.
    """
    if get_settings().codegen_mock:
        return _MOCK_REVIEW  # R10: no Bedrock call
    try:
        resp = _client().invoke(_build_review_prompt(inputs))
    except Exception as exc:
        raise GenerationError(f"review LLM call failed: {exc}") from exc
    text = _content_text(resp).strip()
    if not text:
        raise GenerationError("review response was empty")
    return GenFile(path="REVIEW.md", content=text)

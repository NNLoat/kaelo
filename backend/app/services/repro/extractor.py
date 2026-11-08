"""Setup_Extractor — Bedrock via LangChain (R3). No scoring logic.

Extracts the Experiment Setup from Reader-side index material only (title +
abstract, R3.1/R3.4). Each field is None when unsupported, never fabricated
(R3.2). Raises on failure/timeout so the seam records the setup unavailable
(R3.3). Model/creds from env (R3.5).
"""

import json
import re

from langchain_aws import ChatBedrock

from app.core.config import get_settings
from app.services.demo.seams import CassetteChat, wrap_chat
from app.services.llm import _content_text
from app.services.repro.types import ExperimentSetupData


def _client() -> ChatBedrock | CassetteChat:
    settings = get_settings()
    return wrap_chat(
        lambda: ChatBedrock(model=settings.bedrock_model_id, region_name=settings.aws_region)
    )


def extract_setup(title: str, abstract: str | None) -> ExperimentSetupData:
    """Extract hyperparameters/datasets/environment from index metadata."""
    prompt = (
        "Extract the experiment setup from this paper's metadata. Report only "
        "what the text supports; use null for anything not mentioned — never "
        "invent values. Reply as JSON: "
        '{"hyperparameters": <string|null>, "datasets": <string|null>, '
        '"environment": <string|null>}.\n\n'
        f"Title: {title}\n"
        f"Abstract: {abstract or '(none)'}"
    )
    resp = _client().invoke(prompt)
    text = _content_text(resp)

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"setup response not JSON: {text!r}")
    data = json.loads(match.group(0))
    return ExperimentSetupData(
        hyperparameters=_clean(data.get("hyperparameters")),
        datasets=_clean(data.get("datasets")),
        environment=_clean(data.get("environment")),
    )


def _clean(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None

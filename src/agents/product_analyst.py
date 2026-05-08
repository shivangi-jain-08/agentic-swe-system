from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ..benchmarking.instrumentation import instrument_agent
from .common import call_agent, sha256_text


class PAOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature_summary: str
    acceptance_criteria: list[str]
    constraints: list[str]
    out_of_scope: list[str]
    input_hash: str
    output_hash: str


class _PADraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature_summary: str
    acceptance_criteria: list[str]
    constraints: list[str]
    out_of_scope: list[str]


@instrument_agent("product_analyst")
def analyze(*, task: str, model: str, max_retries: int = 2, run_id: str) -> PAOutput:
    system_prompt = "You are the Product Analyst agent. Return ONLY JSON matching the schema."
    user_prompt = (
        f"High-level request:\n{task}\n\n"
        "Return JSON with: feature_summary, acceptance_criteria (list), constraints (list), out_of_scope (list)."
    )

    input_hash = sha256_text(task)
    draft = call_agent(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_model=_PADraft,
        max_retries=max_retries,
    )

    out_data = draft.model_dump()
    out_data["input_hash"] = input_hash
    out_data["output_hash"] = sha256_text(str(out_data))
    return PAOutput.model_validate(out_data)

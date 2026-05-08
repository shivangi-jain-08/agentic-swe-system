from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..benchmarking.instrumentation import instrument_agent
from .common import call_agent, sha256_text


class SubTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    files_to_touch: list[str] = Field(default_factory=list)
    estimated_complexity: str


class TLOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    architecture_notes: str
    subtasks: list[SubTask]
    risks: list[str]
    input_hash: str
    output_hash: str


class _TLDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    architecture_notes: str
    subtasks: list[SubTask]
    risks: list[str]


@instrument_agent("tech_lead")
def plan(
    *,
    task: str,
    model: str,
    max_subtasks: int = 5,
    max_retries: int = 2,
    run_id: str,
) -> TLOutput:
    system_prompt = "You are the Tech Lead agent. Return ONLY JSON matching the schema."
    user_prompt = (
        f"High-level request:\n{task}\n\n"
        f"Constraints: cap subtasks at {max_subtasks}.\n\n"
        "Return JSON with: architecture_notes, subtasks[{id, description, files_to_touch, estimated_complexity}], risks."
    )

    input_hash = sha256_text(task)
    draft = call_agent(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_model=_TLDraft,
        max_retries=max_retries,
    )

    out_data = draft.model_dump()
    out_data["subtasks"] = out_data.get("subtasks", [])[:max_subtasks]
    out_data["input_hash"] = input_hash
    out_data["output_hash"] = sha256_text(str(out_data))
    return TLOutput.model_validate(out_data)

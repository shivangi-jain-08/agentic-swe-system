from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ..benchmarking.instrumentation import instrument_agent
from .common import call_agent, sha256_text


class FileDiff(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str
    unified_diff: str


class DeveloperOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files_to_modify: list[str]
    diffs: list[FileDiff]
    rationale: str
    input_hash: str
    output_hash: str


class _DeveloperDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files_to_modify: list[str]
    diffs: list[FileDiff]
    rationale: str


@instrument_agent("developer")
def develop(
    *,
    task: str,
    context: str,
    model: str,
    max_retries: int = 2,
    run_id: str,
) -> DeveloperOutput:
    system_prompt = (
        "You are the Developer agent. Produce ONLY valid JSON matching the schema. "
        "Generate unified diffs that apply cleanly."
    )
    user_prompt = (
        f"Task:\n{task}\n\n"
        f"Context:\n{context}\n\n"
        "Return a JSON object with: files_to_modify, diffs[{file_path, unified_diff}], rationale."
    )

    input_hash = sha256_text(task + "\n" + context)
    draft = call_agent(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_model=_DeveloperDraft,
        max_retries=max_retries,
    )

    out_data = draft.model_dump()
    out_data["input_hash"] = input_hash
    out_data["output_hash"] = sha256_text(str(out_data))
    return DeveloperOutput.model_validate(out_data)

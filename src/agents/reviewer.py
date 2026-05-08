from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from ..benchmarking.instrumentation import instrument_agent
from .common import call_agent, sha256_text


class ReviewerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject"]
    issues: list[str]
    required_changes: list[str]
    input_hash: str
    output_hash: str

    @model_validator(mode="after")
    def enforce_hard_reject_gate(self) -> ReviewerOutput:
        if self.required_changes and self.decision == "approve":
            raise ValueError(
                "required_changes is non-empty — decision must be 'reject'. "
                "This is a schema constraint, not a prompt instruction."
            )
        return self


class _ReviewerDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject"]
    issues: list[str]
    required_changes: list[str]


@instrument_agent("reviewer")
def review(
    *,
    task: str,
    unified_diffs: str,
    model: str,
    max_retries: int = 2,
    run_id: str,
) -> ReviewerOutput:
    system_prompt = (
        "You are the Reviewer agent. Produce ONLY valid JSON matching the schema. "
        "Be strict: if changes are required, decision must be reject."
    )
    user_prompt = (
        f"Task:\n{task}\n\n"
        f"Unified diff(s):\n{unified_diffs}\n\n"
        "Return JSON with: decision, issues, required_changes."
    )

    input_hash = sha256_text(task + "\n" + unified_diffs)
    draft = call_agent(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_model=_ReviewerDraft,
        max_retries=max_retries,
    )

    out_data = draft.model_dump()
    out_data["input_hash"] = input_hash
    out_data["output_hash"] = sha256_text(str(out_data))
    return ReviewerOutput.model_validate(out_data)

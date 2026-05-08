from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ..agents.common import call_agent
from ..sop.mutation import SOPMutation
from ..sop.schema import SOPConfig
from .diagnostic import DiagnosticOutput


class ArchitectOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mutations: list[SOPMutation]


class _ArchitectDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mutations: list[SOPMutation]


def propose_mutations(
    *,
    diagnosis: DiagnosticOutput,
    sop: SOPConfig,
    model: str,
    max_retries: int = 2,
) -> list[SOPMutation]:
    """Propose typed SOPMutation objects for a given diagnosis.

    This is intentionally constrained: mutations must validate against the SOP schema.
    """

    system_prompt = (
        "You are the SOP Architect agent. Return ONLY JSON matching the schema. "
        "Propose a small set of SOPMutations."
    )

    user_prompt = (
        f"Diagnosis:\n{diagnosis.model_dump()}\n\n"
        f"Current SOP:\n{sop.model_dump()}\n\n"
        "Return JSON with: mutations[{field_path, current_value, proposed_value, rationale}]."
    )

    draft = call_agent(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_model=_ArchitectDraft,
        max_retries=max_retries,
    )

    return draft.mutations

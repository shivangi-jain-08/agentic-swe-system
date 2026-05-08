from __future__ import annotations

from typing import TypedDict

from ..agents.developer import DeveloperOutput
from ..agents.product_analyst import PAOutput
from ..agents.qa import QAOutput
from ..agents.reviewer import ReviewerOutput
from ..agents.tech_lead import TLOutput
from ..sop.schema import SOPConfig


class PipelineState(TypedDict, total=False):
    # Input
    task: str
    sop: SOPConfig
    run_id: str
    repo_path: str

    # Planning layer (optional)
    pa_output: PAOutput | None
    tl_output: TLOutput | None
    current_subtask_id: str | None

    # Inner loop
    current_diff: DeveloperOutput | None
    reviewer_output: ReviewerOutput | None
    qa_output: QAOutput | None
    retry_count: int

    # Aggregation
    loop_status: str  # running | completed | failed | retry_exhausted
    all_qa_outputs: list[QAOutput]

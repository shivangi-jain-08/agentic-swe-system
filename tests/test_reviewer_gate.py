import pytest
from pydantic import ValidationError

from src.agents.reviewer import ReviewerOutput


def test_reviewer_gate_rejects_approve_with_required_changes() -> None:
    with pytest.raises(ValidationError):
        ReviewerOutput(
            decision="approve",
            issues=["x"],
            required_changes=["must fix"],
            input_hash="in",
            output_hash="out",
        )

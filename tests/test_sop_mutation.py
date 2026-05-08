import pytest
from pydantic import ValidationError

from src.sop.mutation import SOPMutation


def test_sop_mutation_field_path_validation() -> None:
    # Known-good path
    SOPMutation(
        field_path="retry_limits.loop",
        current_value=3,
        proposed_value=2,
        rationale="tighten",
    )

    # Unknown path should fail validation
    with pytest.raises(ValidationError):
        SOPMutation(
            field_path="does.not.exist",
            current_value=1,
            proposed_value=2,
            rationale="nope",
        )

from pathlib import Path

from src.sop.schema import SOPConfig


def test_sop_loads(tmp_path: Path) -> None:
    p = tmp_path / "sop.yaml"
    p.write_text(
        """
version: "1.0.0"
agent_order: [developer, reviewer, qa]
model_assignments:
  developer: deepseek-coder:6.7b
  reviewer: deepseek-coder:6.7b
retry_limits:
  developer: 2
  loop: 3
stop_conditions:
  max_subtasks: 5
  qa_pass_threshold: 0.8
feature_flags:
  use_product_analyst: true
  use_tech_lead: true
""".lstrip(),
        encoding="utf-8",
    )

    sop = SOPConfig.from_yaml(p)
    assert sop.version == "1.0.0"
    assert sop.retry_limits.loop == 3

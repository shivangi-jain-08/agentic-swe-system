from __future__ import annotations

import argparse
import os

from ..sop.schema import SOPConfig
from .inner_loop import run_task


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic SWE System")
    parser.add_argument("--task", required=True, help="High-level coding task")
    parser.add_argument(
        "--sop",
        default=os.getenv("SOP_PATH", "./sop/v1.0.yaml"),
        help="Path to SOP yaml",
    )
    parser.add_argument(
        "--repo",
        default=os.getenv("TEST_REPO_PATH", "./repos/httpie"),
        help="Path to the target repo under test",
    )
    parser.add_argument("--task-id", default="adhoc", help="Task id for benchmarking")

    args = parser.parse_args()
    sop = SOPConfig.from_yaml(args.sop)

    final_state = run_task(
        task=args.task,
        sop=sop,
        repo_path=args.repo,
        task_id=args.task_id,
    )
    qa = final_state.get("qa_output")
    if qa:
        print("QA:", qa.model_dump())
    else:
        print("Final state:", final_state)


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class QAOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_pass_rate: float
    lint_score: float
    cyclomatic_complexity: float
    coverage_delta: float
    test_errors: list[str]


def run_qa(repo_path: str) -> QAOutput:
    """Run deterministic QA metrics. This function must never call an LLM."""

    repo = Path(repo_path)
    if not repo.exists():
        raise FileNotFoundError(repo_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        report_path = tmp_path / "pytest_report.json"
        coverage_path = tmp_path / "coverage.json"

        # 1) pytest (json report)
        pytest_cmd = [
            "pytest",
            "--tb=short",
            "--json-report",
            f"--json-report-file={report_path}",
            "--cov",
            f"--cov-report=json:{coverage_path}",
            "-q",
        ]

        result = subprocess.run(
            pytest_cmd,
            cwd=str(repo),
            capture_output=True,
            text=True,
        )

        if report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
        else:
            report = {"summary": {"total": 1, "passed": 0}, "tests": []}

        total = int(report.get("summary", {}).get("total", 1) or 1)
        passed = int(report.get("summary", {}).get("passed", 0) or 0)
        test_pass_rate = float(passed) / float(total) if total else 0.0
        failed_names = [
            t.get("nodeid", "<unknown>")
            for t in report.get("tests", [])
            if t.get("outcome") == "failed"
        ]

        # 2) pylint score (best-effort)
        lint_score = _run_pylint_score(repo)

        # 3) radon cyclomatic complexity (best-effort)
        cyclomatic_complexity = _avg_complexity(repo)

        # 4) coverage delta placeholder (requires baseline capture)
        coverage_delta = 0.0

        # If pytest invocation failed but report exists, still surface failures.
        if result.returncode != 0 and not failed_names:
            failed_names = ["pytest_failed (no json test list)"]

        return QAOutput(
            test_pass_rate=test_pass_rate,
            lint_score=lint_score,
            cyclomatic_complexity=cyclomatic_complexity,
            coverage_delta=coverage_delta,
            test_errors=failed_names,
        )


def _run_pylint_score(repo: Path) -> float:
    """Return pylint score 0.0–10.0, or 0.0 if pylint is unavailable."""

    try:
        cmd = [
            "python",
            "-m",
            "pylint",
            str(repo),
            "--score=y",
            "--output-format=text",
            "-j0",
        ]
        proc = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True)
        out = proc.stdout + "\n" + proc.stderr

        marker = "rated at"
        for line in out.splitlines():
            if marker in line:
                # Example: "Your code has been rated at 9.50/10"
                try:
                    score_part = line.split(marker, 1)[1].strip()
                    score_str = score_part.split("/", 1)[0].strip()
                    return float(score_str)
                except Exception:
                    continue
        return 0.0
    except Exception:
        return 0.0


def _avg_complexity(repo: Path) -> float:
    try:
        from radon.complexity import cc_visit
    except Exception:
        return 0.0

    complexities: list[float] = []
    for py in repo.rglob("*.py"):
        try:
            results = cc_visit(py.read_text(encoding="utf-8", errors="ignore"))
            complexities.extend([float(r.complexity) for r in results])
        except Exception:
            continue

    return sum(complexities) / len(complexities) if complexities else 0.0

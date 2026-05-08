from __future__ import annotations

import os
from typing import Any

import duckdb
from pydantic import BaseModel, ConfigDict

DB_PATH = os.getenv("DUCKDB_PATH", "./benchmark.db")

METRIC_TO_AGENT = {
    "test_pass_rate": "developer",
    "lint_score": "developer",
    "cyclomatic_complexity": "developer",
    "rejection_rate": "reviewer",
    "wall_clock_ms": "developer",
    "token_cost": "developer",
    "coverage_delta": "developer",
}


class DiagnosticOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weak_metric: str
    delta_vs_median: float
    contributing_agent: str
    hypothesized_cause: str
    suggested_sop_field: str
    current_value: Any
    proposed_value: Any


def diagnose(run_id: str) -> DiagnosticOutput:
    """Identify the weakest metric by comparing a run to historical medians (SQL-only)."""

    con = duckdb.connect(DB_PATH, read_only=True)

    current = con.execute(
        "SELECT test_pass_rate, lint_score, cyclomatic_complexity, rejection_rate, "
        "wall_clock_ms, token_cost, coverage_delta FROM metrics WHERE run_id = ?",
        [run_id],
    ).fetchone()
    if not current:
        con.close()
        raise ValueError(f"run_id {run_id} not found")

    medians = con.execute(
        """
        SELECT
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY test_pass_rate),
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY lint_score),
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cyclomatic_complexity),
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rejection_rate),
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY wall_clock_ms),
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY token_cost),
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY coverage_delta)
        FROM metrics
        """
    ).fetchone()

    con.close()

    metrics = [
        "test_pass_rate",
        "lint_score",
        "cyclomatic_complexity",
        "rejection_rate",
        "wall_clock_ms",
        "token_cost",
        "coverage_delta",
    ]
    higher_is_better = {"test_pass_rate", "lint_score", "coverage_delta"}

    deltas: dict[str, float] = {}
    for i, m in enumerate(metrics):
        if m in higher_is_better:
            deltas[m] = float(medians[i] - current[i])
        else:
            deltas[m] = float(current[i] - medians[i])

    weak_metric = max(deltas, key=deltas.get)

    return DiagnosticOutput(
        weak_metric=weak_metric,
        delta_vs_median=round(deltas[weak_metric], 4),
        contributing_agent=METRIC_TO_AGENT.get(weak_metric, "developer"),
        hypothesized_cause=f"{weak_metric} is {round(deltas[weak_metric], 3)} worse than median",
        suggested_sop_field=f"retry_limits.{METRIC_TO_AGENT.get(weak_metric, 'developer')}",
        current_value=current[metrics.index(weak_metric)],
        proposed_value=None,
    )

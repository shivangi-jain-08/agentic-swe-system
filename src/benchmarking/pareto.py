from __future__ import annotations

import os
from typing import Any

import duckdb


def _db_path() -> str:
    return os.getenv("DUCKDB_PATH", "./benchmark.db")


METRICS = [
    "test_pass_rate",
    "lint_score",
    "cyclomatic_complexity",
    "rejection_rate",
    "wall_clock_ms",
    "token_cost",
    "coverage_delta",
]

HIGHER_IS_BETTER = {"test_pass_rate", "lint_score", "coverage_delta"}


def _get_vector(run_id: str) -> dict[str, Any]:
    con = duckdb.connect(_db_path(), read_only=True)
    row = con.execute("SELECT * FROM metrics WHERE run_id = ?", [run_id]).fetchone()
    cols = [d[0] for d in con.description] if con.description else []
    con.close()
    if not row:
        raise ValueError(f"run_id {run_id} not found in metrics table")
    return dict(zip(cols, row, strict=True))


def _dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    better_on_any = False
    for m in METRICS:
        va, vb = a.get(m), b.get(m)
        if va is None or vb is None:
            return False

        if m in HIGHER_IS_BETTER:
            if va < vb:
                return False
            if va > vb:
                better_on_any = True
        else:
            if va > vb:
                return False
            if va < vb:
                better_on_any = True

    return better_on_any


def compare(run_id_a: str, run_id_b: str) -> dict[str, Any]:
    a, b = _get_vector(run_id_a), _get_vector(run_id_b)
    if _dominates(a, b):
        dominance = "a"
    elif _dominates(b, a):
        dominance = "b"
    else:
        dominance = "neither"

    delta = {
        m: (a.get(m), b.get(m), None if a.get(m) is None else a.get(m) - b.get(m)) for m in METRICS
    }
    return {"dominance": dominance, "delta": delta}


def frontier(run_ids: list[str]) -> list[str]:
    vectors = {rid: _get_vector(rid) for rid in run_ids}
    non_dominated: list[str] = []
    for rid, v in vectors.items():
        if not any(_dominates(vectors[other], v) for other in run_ids if other != rid):
            non_dominated.append(rid)
    return non_dominated

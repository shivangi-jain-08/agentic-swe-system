from pathlib import Path

import duckdb


def test_frontier_basic(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "bench.db"
    monkeypatch.setenv("DUCKDB_PATH", str(db))

    con = duckdb.connect(str(db))
    con.execute(
        "CREATE TABLE metrics (run_id VARCHAR PRIMARY KEY, test_pass_rate DOUBLE, lint_score DOUBLE, "
        "cyclomatic_complexity DOUBLE, diff_size INTEGER, file_touch_count INTEGER, rejection_rate DOUBLE, "
        "wall_clock_ms INTEGER, token_cost DOUBLE, coverage_delta DOUBLE)"
    )

    # A dominates B, C is non-dominated against A (tradeoff)
    con.execute(
        "INSERT INTO metrics VALUES (?,?,?,?,?,?,?,?,?,?)",
        ["A", 1.0, 10.0, 1.0, 1, 1, 0.0, 100, 1.0, 0.0],
    )
    con.execute(
        "INSERT INTO metrics VALUES (?,?,?,?,?,?,?,?,?,?)",
        ["B", 0.5, 5.0, 2.0, 1, 1, 0.0, 200, 2.0, 0.0],
    )
    con.execute(
        "INSERT INTO metrics VALUES (?,?,?,?,?,?,?,?,?,?)",
        ["C", 1.0, 10.0, 1.0, 1, 1, 0.0, 50, 3.0, 0.0],
    )
    con.close()

    from src.benchmarking.pareto import frontier

    f = frontier(["A", "B", "C"])
    assert "B" not in f
    assert set(f) == {"A", "C"}

from __future__ import annotations

import os
from pathlib import Path

import duckdb


def init_db(db_path: str | None = None) -> str:
    """Initialize benchmark DuckDB schema and return the resolved path."""

    resolved = str(Path(db_path or os.getenv("DUCKDB_PATH", "./benchmark.db")))
    schema_path = Path(__file__).with_name("schema.sql")
    con = duckdb.connect(resolved)
    con.execute(schema_path.read_text(encoding="utf-8"))
    con.close()
    return resolved

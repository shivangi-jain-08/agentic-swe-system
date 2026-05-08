from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import duckdb

from .db import init_db

T = TypeVar("T")


def instrument_agent(agent_role: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that logs one row to `agent_events` per agent invocation."""

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            db_path = init_db(os.getenv("DUCKDB_PATH", "./benchmark.db"))
            run_id = kwargs.get("run_id") or (args[0] if args else "unknown")

            input_hash = hashlib.sha256(
                json.dumps({"args": args, "kwargs": kwargs}, default=str).encode("utf-8")
            ).hexdigest()
            start = time.monotonic()
            result = fn(*args, **kwargs)
            latency_ms = int((time.monotonic() - start) * 1000)
            output_hash = hashlib.sha256(
                json.dumps(result, default=str).encode("utf-8")
            ).hexdigest()

            decision = getattr(result, "decision", None)
            rejection_reason = None
            if decision == "reject":
                rejection_reason = "; ".join(getattr(result, "required_changes", []) or []) or None

            con = duckdb.connect(db_path)
            con.execute(
                "INSERT INTO agent_events VALUES (?,?,?,?,?,?,?,?,?)",
                [
                    str(uuid.uuid4()),
                    str(run_id),
                    agent_role,
                    input_hash,
                    output_hash,
                    decision,
                    latency_ms,
                    None,
                    rejection_reason,
                ],
            )
            con.close()
            return result

        return wrapper

    return decorator

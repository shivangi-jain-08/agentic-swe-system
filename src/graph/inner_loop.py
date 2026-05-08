from __future__ import annotations

import os
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import duckdb
from langgraph.graph import END, StateGraph

from ..agents.developer import develop
from ..agents.qa import run_qa
from ..agents.reviewer import review
from ..benchmarking.db import init_db
from ..executor.git_executor import apply_diff, cleanup
from ..rag.call_graph import build as build_call_graph
from ..rag.indexer import resolve_default_paths
from ..rag.retriever import query as retrieve
from ..sop.schema import SOPConfig
from .state import PipelineState


def build_graph(sop: SOPConfig):
    g = StateGraph(PipelineState)

    g.add_node("developer", developer_node)
    g.add_node("reviewer", reviewer_node)
    g.add_node("qa", qa_node)

    g.set_entry_point("developer")
    g.add_edge("developer", "reviewer")

    def route_reviewer(state: PipelineState) -> str:
        out = state.get("reviewer_output")
        if out and out.decision == "approve":
            return "qa"
        retry_count = int(state.get("retry_count", 0))
        if retry_count >= int(state["sop"].retry_limits.loop):
            return "fail"
        return "developer"

    g.add_conditional_edges(
        "reviewer",
        route_reviewer,
        {
            "qa": "qa",
            "developer": "developer",
            "fail": END,
        },
    )

    g.add_edge("qa", END)
    return g.compile()


def developer_node(state: PipelineState) -> PipelineState:
    task = state["task"]
    sop = state["sop"]
    repo_path = state["repo_path"]

    context = _build_rag_context(task=task, repo_path=repo_path)
    model = os.getenv("DEVELOPER_MODEL", sop.model_assignments.developer)

    out = develop(
        task=task,
        context=context,
        model=model,
        max_retries=sop.retry_limits.developer,
        run_id=state["run_id"],
    )
    state["current_diff"] = out
    return state


def reviewer_node(state: PipelineState) -> PipelineState:
    task = state["task"]
    sop = state["sop"]
    model = os.getenv("REVIEWER_MODEL", sop.model_assignments.reviewer)

    current = state.get("current_diff")
    unified = "\n\n".join(d.unified_diff for d in (current.diffs if current else []))

    out = review(
        task=task,
        unified_diffs=unified,
        model=model,
        max_retries=sop.retry_limits.developer,
        run_id=state["run_id"],
    )
    state["reviewer_output"] = out

    if out.decision == "reject":
        state["retry_count"] = int(state.get("retry_count", 0)) + 1

    return state


def qa_node(state: PipelineState) -> PipelineState:
    repo_path = state["repo_path"]
    run_id = state["run_id"]

    diff = state.get("current_diff")
    branch_name = f"agentic-swe/{run_id[:8]}-{int(state.get('retry_count', 0))}"

    start = time.monotonic()
    db_path = init_db(os.getenv("DUCKDB_PATH", "./benchmark.db"))

    try:
        if diff:
            apply_diff(repo_path, branch_name, diff.diffs)
        qa = run_qa(repo_path)
        state["qa_output"] = qa
        _write_metrics(db_path, run_id, qa, diff)
        state["loop_status"] = "completed"
        return state
    finally:
        # Always attempt cleanup.
        try:
            cleanup(repo_path, branch_name)
        except Exception:
            pass
        elapsed_ms = int((time.monotonic() - start) * 1000)
        _mark_run_completed(
            db_path,
            run_id,
            elapsed_ms,
            status=state.get("loop_status", "completed"),
        )


def run_task(*, task: str, sop: SOPConfig, repo_path: str, task_id: str = "adhoc") -> PipelineState:
    db_path = init_db(os.getenv("DUCKDB_PATH", "./benchmark.db"))
    run_id = str(uuid.uuid4())

    con = duckdb.connect(db_path)
    con.execute(
        "INSERT INTO runs VALUES (?,?,?,?,?,?)",
        [run_id, sop.version, task_id, datetime.now(UTC), "running", None],
    )
    con.close()

    graph = build_graph(sop)
    state: PipelineState = {
        "task": task,
        "sop": sop,
        "run_id": run_id,
        "repo_path": repo_path,
        "retry_count": 0,
        "loop_status": "running",
        "all_qa_outputs": [],
    }

    return graph.invoke(state)


def _build_rag_context(*, task: str, repo_path: str) -> str:
    faiss_path, chunks_db_path = resolve_default_paths()
    if not Path(faiss_path).exists() or not Path(chunks_db_path).exists():
        return ""

    call_graph = build_call_graph(repo_path)
    chunks = retrieve(
        query_str=task,
        faiss_path=faiss_path,
        db_path=chunks_db_path,
        call_graph=call_graph,
        context_budget_tokens=2000,
        top_k=10,
    )

    parts: list[str] = []
    for c in chunks:
        header = f"[{c.chunk_type}] {c.symbol_name} ({c.file_path}:{c.start_line}-{c.end_line})"
        parts.append(header + "\n" + c.raw_code)

    return "\n\n".join(parts)


def _write_metrics(db_path: str, run_id: str, qa, diff) -> None:
    con = duckdb.connect(db_path)
    diff_size = 0
    file_touch_count = 0
    if diff:
        file_touch_count = len({d.file_path for d in diff.diffs})
        diff_size = sum(len(d.unified_diff.splitlines()) for d in diff.diffs)

    con.execute(
        "INSERT OR REPLACE INTO metrics VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            run_id,
            qa.test_pass_rate,
            qa.lint_score,
            qa.cyclomatic_complexity,
            diff_size,
            file_touch_count,
            None,
            None,
            None,
            qa.coverage_delta,
        ],
    )
    con.close()


def _mark_run_completed(db_path: str, run_id: str, wall_clock_ms: int, status: str) -> None:
    con = duckdb.connect(db_path)
    con.execute(
        "UPDATE runs SET status = ? WHERE run_id = ?",
        [status, run_id],
    )

    con.execute(
        "UPDATE metrics SET wall_clock_ms = ? WHERE run_id = ?",
        [wall_clock_ms, run_id],
    )
    con.close()

from __future__ import annotations

import copy
import os
from collections.abc import Callable

import duckdb
import semver

from ..benchmarking.pareto import frontier
from ..sop.mutation import SOPMutation
from ..sop.schema import SOPConfig
from .architect import propose_mutations
from .diagnostic import diagnose

DB_PATH = os.getenv("DUCKDB_PATH", "./benchmark.db")
MAX_ITERATIONS = 5


def run_improvement_loop(
    *,
    starting_sop: SOPConfig,
    task_ids: list[str],
    run_all_tasks: Callable[[SOPConfig, list[str]], list[str]],
    max_iterations: int = MAX_ITERATIONS,
    architect_model: str,
) -> SOPConfig:
    """Hill-climb SOP config (hard-capped) using Pareto selection."""

    current_sop = starting_sop

    for _iteration in range(min(max_iterations, MAX_ITERATIONS)):
        run_ids = run_all_tasks(current_sop, task_ids)
        worst_run_id = _pick_worst_run(run_ids)

        diagnosis = diagnose(worst_run_id)
        mutations = propose_mutations(
            diagnosis=diagnosis,
            sop=current_sop,
            model=architect_model,
        )

        candidate_sop = _apply_mutations(current_sop, mutations)
        candidate_run_ids = run_all_tasks(candidate_sop, task_ids)

        # Keep candidate if it appears on the frontier of combined runs.
        combined = run_ids + candidate_run_ids
        keepers = set(frontier(combined))
        if any(rid in keepers for rid in candidate_run_ids):
            current_sop = candidate_sop

    return current_sop


def _apply_mutations(sop: SOPConfig, mutations: list[SOPMutation]) -> SOPConfig:
    data = copy.deepcopy(sop.model_dump())

    for m in mutations:
        parts = m.field_path.split(".")
        node = data
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = m.proposed_value

    new_version = str(semver.Version.parse(sop.version).bump_patch())
    data["version"] = new_version

    candidate = SOPConfig.model_validate(data)
    _record_parent(candidate.version, sop.version)
    return candidate


def _record_parent(sop_version: str, parent_sop_version: str) -> None:
    con = duckdb.connect(DB_PATH)
    con.execute(
        "UPDATE runs SET parent_sop_version = ? WHERE sop_version = ?",
        [parent_sop_version, sop_version],
    )
    con.close()


def _pick_worst_run(run_ids: list[str]) -> str:
    # Placeholder heuristic: caller decides which run is 'worst'.
    # A stronger implementation would rank by a weighted metric vector.
    if not run_ids:
        raise ValueError("No run_ids provided")
    return run_ids[0]

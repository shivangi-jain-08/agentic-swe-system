
# DuckDB Schema

The benchmark database (default `benchmark.db`, configurable via `DUCKDB_PATH`) is initialized from [src/benchmarking/schema.sql](src/benchmarking/schema.sql).

## Tables

### `runs`

| Column | Type | Meaning |
|---|---|---|
| `run_id` | `VARCHAR` | Primary key for a pipeline run |
| `sop_version` | `VARCHAR` | SOP version used for the run |
| `task_id` | `VARCHAR` | Benchmark task id (or ad-hoc label) |
| `timestamp` | `TIMESTAMP` | Run start timestamp |
| `status` | `VARCHAR` | `completed` \| `failed` \| `retry_exhausted` |
| `parent_sop_version` | `VARCHAR` | Parent SOP version (for improvement lineage) |

### `agent_events`

| Column | Type | Meaning |
|---|---|---|
| `event_id` | `VARCHAR` | Primary key for an agent invocation |
| `run_id` | `VARCHAR` | Foreign key to `runs.run_id` |
| `agent_role` | `VARCHAR` | `developer` \| `reviewer` \| `qa` \| `product_analyst` \| `tech_lead` |
| `input_hash` | `VARCHAR` | SHA-256 hash of agent input |
| `output_hash` | `VARCHAR` | SHA-256 hash of agent output |
| `decision` | `VARCHAR` | Reviewer decision (nullable) |
| `latency_ms` | `INTEGER` | End-to-end agent call latency |
| `token_count` | `INTEGER` | Optional token count (nullable) |
| `rejection_reason` | `VARCHAR` | Reviewer rejection details (nullable) |

### `metrics`

| Column | Type | Meaning |
|---|---|---|
| `run_id` | `VARCHAR` | Foreign key to `runs.run_id` |
| `test_pass_rate` | `DOUBLE` | Passed / total from pytest json report |
| `lint_score` | `DOUBLE` | Pylint score (0.0–10.0) |
| `cyclomatic_complexity` | `DOUBLE` | Average complexity (radon) |
| `diff_size` | `INTEGER` | Lines changed |
| `file_touch_count` | `INTEGER` | Distinct files modified |
| `rejection_rate` | `DOUBLE` | Reviewer rejections / reviewer calls |
| `wall_clock_ms` | `INTEGER` | Total run latency |
| `token_cost` | `DOUBLE` | Total tokens/cost (placeholder) |
| `coverage_delta` | `DOUBLE` | Coverage change vs baseline |

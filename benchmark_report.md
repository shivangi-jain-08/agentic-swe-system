# Pipeline Benchmark Report

## Setup
- Task suite: `src/benchmarking/tasks.json` (5 tasks)
- SOP baseline: `sop/v1.0.yaml`
- SOP variant: `sop/v1.1.yaml`
- Runs per SOP: 

## Results

| Metric | v1.0 | v1.1 | Delta |
|---|---:|---:|---:|
| test_pass_rate |  |  |  |
| lint_score |  |  |  |
| cyclomatic_complexity |  |  |  |
| wall_clock_ms |  |  |  |
| token_cost |  |  |  |
| rejection_rate |  |  |  |

## DuckDB query used

```sql
SELECT r.sop_version,
       AVG(m.test_pass_rate) AS avg_test_pass_rate,
       AVG(m.lint_score) AS avg_lint_score,
       AVG(m.wall_clock_ms) AS avg_wall_clock_ms
FROM metrics m
JOIN runs r USING(run_id)
GROUP BY r.sop_version;
```

## Finding
- 

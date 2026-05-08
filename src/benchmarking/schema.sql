CREATE TABLE IF NOT EXISTS runs (
    run_id              VARCHAR PRIMARY KEY,
    sop_version         VARCHAR NOT NULL,
    task_id             VARCHAR NOT NULL,
    timestamp           TIMESTAMP NOT NULL,
    status              VARCHAR NOT NULL,       -- 'completed' | 'failed' | 'retry_exhausted'
    parent_sop_version  VARCHAR                 -- NULL for baseline; set during improvement loop
);

CREATE TABLE IF NOT EXISTS agent_events (
    event_id            VARCHAR PRIMARY KEY,
    run_id              VARCHAR NOT NULL REFERENCES runs(run_id),
    agent_role          VARCHAR NOT NULL,       -- developer | reviewer | qa | product_analyst | tech_lead
    input_hash          VARCHAR NOT NULL,
    output_hash         VARCHAR NOT NULL,
    decision            VARCHAR,                -- reviewer only
    latency_ms          INTEGER NOT NULL,
    token_count         INTEGER,
    rejection_reason    VARCHAR
);

CREATE TABLE IF NOT EXISTS metrics (
    run_id                  VARCHAR NOT NULL REFERENCES runs(run_id),
    test_pass_rate          DOUBLE,
    lint_score              DOUBLE,
    cyclomatic_complexity   DOUBLE,
    diff_size               INTEGER,
    file_touch_count        INTEGER,
    rejection_rate          DOUBLE,
    wall_clock_ms           INTEGER,
    token_cost              DOUBLE,
    coverage_delta          DOUBLE,
    PRIMARY KEY(run_id)
);

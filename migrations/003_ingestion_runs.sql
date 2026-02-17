CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id TEXT PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ NOT NULL,
    source_name TEXT NOT NULL,
    status TEXT NOT NULL,
    raw_written INTEGER NOT NULL,
    canonical_written INTEGER NOT NULL,
    quarantined INTEGER NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_finished_at
ON ingestion_runs (finished_at DESC);

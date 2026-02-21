CREATE TABLE IF NOT EXISTS macro_analysis_results (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL,
    as_of TIMESTAMPTZ NOT NULL,
    regime TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    base_case TEXT NOT NULL,
    bull_case TEXT NOT NULL,
    bear_case TEXT NOT NULL,
    reason_codes JSONB NOT NULL,
    risk_flags JSONB NOT NULL,
    triggers JSONB NOT NULL,
    narrative TEXT NOT NULL,
    model TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_macro_analysis_results_as_of_created
ON macro_analysis_results(as_of DESC, created_at DESC);

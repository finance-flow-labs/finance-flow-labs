CREATE TABLE IF NOT EXISTS investment_theses (
    thesis_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT NOT NULL DEFAULT 'system',
    scope_level TEXT NOT NULL CHECK (scope_level IN ('macro', 'sector', 'stock', 'portfolio')),
    target_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    evidence_hard JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_soft JSONB NOT NULL DEFAULT '[]'::jsonb,
    as_of TIMESTAMPTZ NOT NULL,
    lineage_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS forecast_records (
    id BIGSERIAL PRIMARY KEY,
    thesis_id TEXT NOT NULL REFERENCES investment_theses(thesis_id),
    horizon TEXT NOT NULL CHECK (horizon IN ('1W', '1M', '3M')),
    expected_return_low DOUBLE PRECISION NOT NULL,
    expected_return_high DOUBLE PRECISION NOT NULL,
    expected_volatility DOUBLE PRECISION,
    expected_drawdown DOUBLE PRECISION,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    key_drivers JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_hard JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_soft JSONB NOT NULL DEFAULT '[]'::jsonb,
    as_of TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (expected_return_low <= expected_return_high)
);

CREATE TABLE IF NOT EXISTS realization_records (
    id BIGSERIAL PRIMARY KEY,
    forecast_id BIGINT NOT NULL REFERENCES forecast_records(id),
    realized_return DOUBLE PRECISION NOT NULL,
    realized_volatility DOUBLE PRECISION,
    max_drawdown DOUBLE PRECISION,
    hit BOOLEAN NOT NULL,
    forecast_error DOUBLE PRECISION NOT NULL,
    evaluated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS forecast_error_attributions (
    id BIGSERIAL PRIMARY KEY,
    realization_id BIGINT NOT NULL REFERENCES realization_records(id),
    category TEXT NOT NULL CHECK (
        category IN (
            'data_lag',
            'regime_shift',
            'valuation_miss',
            'macro_miss',
            'execution_slippage',
            'risk_control_failure',
            'unknown'
        )
    ),
    contribution DOUBLE PRECISION,
    note TEXT,
    evidence_hard JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_soft JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forecast_records_thesis_horizon
ON forecast_records(thesis_id, horizon, as_of DESC);

CREATE INDEX IF NOT EXISTS idx_realization_records_forecast_evaluated
ON realization_records(forecast_id, evaluated_at DESC);

CREATE INDEX IF NOT EXISTS idx_error_attributions_realization_category
ON forecast_error_attributions(realization_id, category);

CREATE TABLE IF NOT EXISTS macro_series_points (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    as_of TIMESTAMPTZ NOT NULL,
    available_at TIMESTAMPTZ NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    lineage_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_macro_series_metric_asof
ON macro_series_points(metric_key, as_of DESC);

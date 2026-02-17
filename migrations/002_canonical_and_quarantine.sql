CREATE TABLE IF NOT EXISTS canonical_fact_store (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    as_of TIMESTAMPTZ NOT NULL,
    available_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    license_tier TEXT NOT NULL,
    lineage_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC,
    schema_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quarantine_batches (
    id BIGSERIAL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

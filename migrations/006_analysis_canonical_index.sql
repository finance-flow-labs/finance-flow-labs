-- Composite index for fast canonical fact lookups by the analysis layer.
-- Used by CanonicalDataClient.read_series(source, metric_name, limit).
CREATE INDEX IF NOT EXISTS idx_canonical_source_metric_asof
    ON canonical_fact_store (source, metric_name, as_of DESC);

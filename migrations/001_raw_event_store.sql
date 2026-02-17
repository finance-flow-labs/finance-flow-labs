CREATE TABLE IF NOT EXISTS raw_event_store (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    as_of TIMESTAMPTZ NOT NULL,
    available_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    lineage_id TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    license_tier TEXT NOT NULL,
    payload JSONB NOT NULL,
    is_superseded BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_raw_event_entity_asof ON raw_event_store (entity_id, as_of);
CREATE INDEX IF NOT EXISTS idx_raw_event_available ON raw_event_store (available_at);

CREATE OR REPLACE FUNCTION prevent_raw_event_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'raw_event_store is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_raw_event_update ON raw_event_store;
CREATE TRIGGER trg_prevent_raw_event_update
BEFORE UPDATE ON raw_event_store
FOR EACH ROW
EXECUTE FUNCTION prevent_raw_event_mutation();

DROP TRIGGER IF EXISTS trg_prevent_raw_event_delete ON raw_event_store;
CREATE TRIGGER trg_prevent_raw_event_delete
BEFORE DELETE ON raw_event_store
FOR EACH ROW
EXECUTE FUNCTION prevent_raw_event_mutation();

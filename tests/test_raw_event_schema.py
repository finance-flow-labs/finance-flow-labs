from pathlib import Path


def test_raw_event_migration_contains_required_columns():
    migration_path = Path("migrations/001_raw_event_store.sql")
    sql = migration_path.read_text(encoding="utf-8")

    required = [
        "source",
        "entity_id",
        "as_of",
        "available_at",
        "ingested_at",
        "lineage_id",
        "schema_version",
        "license_tier",
    ]
    for column in required:
        assert column in sql


def test_raw_event_migration_has_append_only_guard():
    migration_path = Path("migrations/001_raw_event_store.sql")
    sql = migration_path.read_text(encoding="utf-8")
    assert "prevent_raw_event_mutation" in sql


def test_canonical_migration_contains_required_metadata_columns():
    migration_path = Path("migrations/002_canonical_and_quarantine.sql")
    sql = migration_path.read_text(encoding="utf-8")
    assert "ingested_at" in sql
    assert "license_tier" in sql

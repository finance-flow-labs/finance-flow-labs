from pathlib import Path


def test_ingestion_runs_migration_contains_required_columns():
    sql = Path("migrations/003_ingestion_runs.sql").read_text(encoding="utf-8")

    required = [
        "run_id",
        "started_at",
        "finished_at",
        "source_name",
        "status",
        "raw_written",
        "canonical_written",
        "quarantined",
    ]
    for column in required:
        assert column in sql

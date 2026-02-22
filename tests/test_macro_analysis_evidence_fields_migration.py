from pathlib import Path


def test_macro_analysis_results_migration_adds_hard_soft_evidence_fields():
    sql = Path("migrations/009_macro_analysis_evidence_fields.sql").read_text(
        encoding="utf-8"
    )

    assert "ALTER TABLE macro_analysis_results" in sql
    assert "ADD COLUMN IF NOT EXISTS evidence_hard JSONB" in sql
    assert "ADD COLUMN IF NOT EXISTS evidence_soft JSONB" in sql

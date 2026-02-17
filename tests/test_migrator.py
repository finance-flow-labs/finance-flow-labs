import importlib
import sqlite3


migrator_mod = importlib.import_module("src.ingestion.migrator")
MigrationRunner = migrator_mod.MigrationRunner


def test_migrator_applies_pending_files_only(tmp_path):
    migration_dir = tmp_path / "migrations"
    migration_dir.mkdir()

    (migration_dir / "001_create_table.sql").write_text(
        "CREATE TABLE t1 (id INTEGER PRIMARY KEY);", encoding="utf-8"
    )
    (migration_dir / "002_create_table.sql").write_text(
        "CREATE TABLE t2 (id INTEGER PRIMARY KEY);", encoding="utf-8"
    )

    conn = sqlite3.connect(":memory:")
    runner = MigrationRunner(conn=conn, migration_dir=migration_dir)

    first = runner.apply_pending()
    second = runner.apply_pending()

    assert first == ["001_create_table.sql", "002_create_table.sql"]
    assert second == []

    rows = conn.execute("SELECT filename FROM schema_migrations ORDER BY filename").fetchall()
    assert rows == [("001_create_table.sql",), ("002_create_table.sql",)]

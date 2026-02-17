from datetime import datetime, timezone
from pathlib import Path
import sqlite3


class MigrationRunner:
    def __init__(self, conn: sqlite3.Connection, migration_dir: Path) -> None:
        self.conn = conn
        self.migration_dir = migration_dir
        self._ensure_schema_table()

    def _ensure_schema_table(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def _applied(self) -> set[str]:
        rows = self.conn.execute("SELECT filename FROM schema_migrations").fetchall()
        return {row[0] for row in rows}

    def apply_pending(self) -> list[str]:
        applied = self._applied()
        executed: list[str] = []

        for migration_path in sorted(self.migration_dir.glob("*.sql")):
            name = migration_path.name
            if name in applied:
                continue

            sql = migration_path.read_text(encoding="utf-8")
            self.conn.executescript(sql)
            self.conn.execute(
                "INSERT INTO schema_migrations(filename, applied_at) VALUES (?, ?)",
                (name, datetime.now(timezone.utc).isoformat()),
            )
            self.conn.commit()
            executed.append(name)

        return executed

import importlib


postgres_repository = importlib.import_module("src.ingestion.postgres_repository")
PostgresRepository = postgres_repository.PostgresRepository


class FakeCursor:
    def __init__(self, fetch_rows=None, columns=None, fetch_one_rows=None):
        self.fetch_rows = fetch_rows or []
        self.columns = columns or []
        self.fetch_one_rows = fetch_one_rows or []
        self.executed = []
        self.description = [(name,) for name in self.columns]

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return self.fetch_rows

    def fetchone(self):
        if self.fetch_one_rows:
            return self.fetch_one_rows.pop(0)
        return None

    def close(self):
        return None


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.committed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def close(self):
        return None


def test_postgres_repository_builds_insert_payload_for_run_history():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    repo.write_run_history(
        {
            "run_id": "run-1",
            "started_at": "2026-02-18T00:00:00+00:00",
            "finished_at": "2026-02-18T00:01:00+00:00",
            "source_name": "sec_edgar",
            "status": "success",
            "raw_written": 10,
            "canonical_written": 8,
            "quarantined": 2,
            "error_message": None,
        }
    )

    assert "INSERT INTO ingestion_runs" in cursor.executed[0][0]
    assert cursor.executed[0][1][0] == "run-1"
    assert conn.committed is True


def test_postgres_repository_reads_latest_runs():
    cursor = FakeCursor(
        fetch_rows=[("run-1", "success", "2026-02-18T00:01:00+00:00")],
        columns=["run_id", "status", "finished_at"],
    )
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    rows = repo.read_latest_runs(limit=20)

    assert "ORDER BY finished_at DESC" in cursor.executed[0][0]
    assert rows[0]["run_id"] == "run-1"
    assert rows[0]["status"] == "success"


def test_postgres_repository_writes_pipeline_rows_and_reads_counters():
    cursor = FakeCursor(fetch_one_rows=[(3,), (2,), (1,)])
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    repo.write_raw({"source": "sec_edgar", "entity_id": "AAPL"})
    repo.write_canonical({"source": "sec_edgar", "entity_id": "AAPL"})
    repo.write_quarantine("quality_gate_failed", {"source": "sec_edgar"})
    counters = repo.read_status_counters()

    assert "INSERT INTO raw_event_store" in cursor.executed[0][0]
    assert "INSERT INTO canonical_fact_store" in cursor.executed[1][0]
    assert "INSERT INTO quarantine_batches" in cursor.executed[2][0]
    assert counters == {"raw_events": 3, "canonical_events": 2, "quarantine_events": 1}

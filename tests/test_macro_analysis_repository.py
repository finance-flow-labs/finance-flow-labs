import importlib


postgres_repository = importlib.import_module("src.ingestion.postgres_repository")
PostgresRepository = postgres_repository.PostgresRepository


class FakeCursor:
    def __init__(self, fetch_rows=None, columns=None):
        self.fetch_rows = fetch_rows or []
        self.columns = columns or []
        self.executed = []
        self.description = [(name,) for name in self.columns]

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return self.fetch_rows

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


def test_postgres_repository_writes_macro_analysis_result():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    repo.write_macro_analysis_result(
        {
            "run_id": "run-1",
            "as_of": "2026-02-18T00:00:00+00:00",
            "regime": "neutral",
            "confidence": 0.62,
            "base_case": "growth slows with sticky inflation",
            "bull_case": "soft landing",
            "bear_case": "policy mistake",
            "reason_codes": ["cpi_cooling", "rate_plateau"],
            "risk_flags": ["data_gap"],
            "triggers": ["next_cpi", "fomc_minutes"],
            "narrative": "Macro conditions are mixed with a slight slowdown bias.",
            "model": "gpt-5.3-codex",
        }
    )

    assert "INSERT INTO macro_analysis_results" in cursor.executed[0][0]
    assert cursor.executed[0][1][0] == "run-1"
    assert conn.committed is True


def test_postgres_repository_reads_latest_macro_analysis():
    cursor = FakeCursor(
        fetch_rows=[
            (
                "run-1",
                "2026-02-18T00:00:00+00:00",
                "neutral",
                0.62,
                "growth slows",
                "soft landing",
                "hard landing",
                ["cpi_cooling"],
                ["data_gap"],
                ["next_cpi"],
                "narrative text",
                "gpt-5.3-codex",
                "2026-02-18T00:01:00+00:00",
            )
        ],
        columns=[
            "run_id",
            "as_of",
            "regime",
            "confidence",
            "base_case",
            "bull_case",
            "bear_case",
            "reason_codes",
            "risk_flags",
            "triggers",
            "narrative",
            "model",
            "created_at",
        ],
    )
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    rows = repo.read_latest_macro_analysis(limit=10)

    assert "FROM macro_analysis_results" in cursor.executed[0][0]
    assert rows[0]["run_id"] == "run-1"
    assert rows[0]["regime"] == "neutral"

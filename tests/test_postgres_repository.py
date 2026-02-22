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


def test_postgres_repository_writes_investment_thesis_and_returns_id():
    cursor = FakeCursor(fetch_one_rows=[("thesis-1",)])
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    thesis_id = repo.write_investment_thesis(
        {
            "thesis_id": "thesis-1",
            "created_by": "autopilot",
            "scope_level": "stock",
            "target_id": "AAPL",
            "title": "AI capex cycle persists",
            "summary": "Cloud demand and margins support overweight.",
            "evidence_hard": [{"source": "sec", "metric": "revenue_growth"}],
            "evidence_soft": [{"source": "news", "note": "management tone improved"}],
            "as_of": "2026-02-22T00:00:00+00:00",
            "lineage_id": "lineage-1",
        }
    )

    assert thesis_id == "thesis-1"
    assert "INSERT INTO investment_theses" in cursor.executed[0][0]
    assert "ON CONFLICT (thesis_id) DO UPDATE" in cursor.executed[0][0]
    assert conn.committed is True


def test_postgres_repository_writes_forecast_record_and_returns_id():
    cursor = FakeCursor(fetch_one_rows=[(42,)])
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    forecast_id = repo.write_forecast_record(
        {
            "thesis_id": "thesis-1",
            "horizon": "1M",
            "expected_return_low": 0.04,
            "expected_return_high": 0.10,
            "expected_volatility": 0.2,
            "expected_drawdown": 0.12,
            "confidence": 0.7,
            "key_drivers": ["macro:disinflation"],
            "evidence_hard": [{"source": "fred", "metric": "CPI"}],
            "evidence_soft": [{"source": "news", "note": "AI capex sentiment"}],
            "as_of": "2026-02-22T00:00:00+00:00",
        }
    )

    assert forecast_id == 42
    assert "INSERT INTO forecast_records" in cursor.executed[0][0]
    assert conn.committed is True


def test_postgres_repository_computes_realization_hit_and_forecast_error_from_forecast_range():
    cursor = FakeCursor(fetch_one_rows=[(0.02, 0.08), (99,)])
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    realization_id = repo.write_realization_from_outcome(
        forecast_id=7,
        realized_return=0.05,
        evaluated_at="2026-03-22T00:00:00+00:00",
        realized_volatility=0.18,
        max_drawdown=0.09,
    )

    assert realization_id == 99
    assert "SELECT expected_return_low, expected_return_high" in cursor.executed[0][0]
    insert_sql, insert_params = cursor.executed[1]
    assert "INSERT INTO realization_records" in insert_sql
    # midpoint(0.02, 0.08)=0.05, so forecast_error should be 0.0 and hit=True
    assert insert_params[4] is True
    assert insert_params[5] == 0.0


def test_postgres_repository_writes_forecast_error_attribution_and_returns_id():
    cursor = FakeCursor(fetch_one_rows=[(321,)])
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    attribution_id = repo.write_forecast_error_attribution(
        {
            "realization_id": 99,
            "category": "macro_miss",
            "contribution": -0.03,
            "note": "inflation re-acceleration",
            "evidence_hard": [{"source": "fred", "metric": "CPI"}],
            "evidence_soft": [{"source": "analyst", "note": "policy surprise"}],
        }
    )

    assert attribution_id == 321
    assert "INSERT INTO forecast_error_attributions" in cursor.executed[0][0]
    assert conn.committed is True


def test_postgres_repository_raises_when_forecast_missing_for_realization_write():
    cursor = FakeCursor(fetch_one_rows=[None])
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    try:
        repo.write_realization_from_outcome(
            forecast_id=123,
            realized_return=0.01,
            evaluated_at="2026-03-22T00:00:00+00:00",
        )
    except ValueError as exc:
        assert "forecast_id not found" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing forecast_id")


def test_postgres_repository_reads_expected_vs_realized_with_evidence_fields():
    cursor = FakeCursor(
        fetch_rows=[
            (
                7,
                "1M",
                "2026-02-22T00:00:00+00:00",
                0.02,
                0.08,
                0.2,
                0.12,
                0.7,
                [{"driver": "macro:disinflation"}],
                [{"source": "fred", "metric": "CPI"}],
                [{"source": "news", "note": "tone improved"}],
                99,
                0.05,
                0.18,
                0.09,
                True,
                0.0,
                "2026-03-22T00:00:00+00:00",
                "thesis-1",
                "stock",
                "AAPL",
                "AI capex cycle persists",
                "Cloud demand supports overweight.",
                [{"source": "sec", "metric": "revenue_growth"}],
                [{"source": "news", "note": "management tone improved"}],
            )
        ],
        columns=[
            "forecast_id",
            "horizon",
            "as_of",
            "expected_return_low",
            "expected_return_high",
            "expected_volatility",
            "expected_drawdown",
            "confidence",
            "key_drivers",
            "forecast_evidence_hard",
            "forecast_evidence_soft",
            "realization_id",
            "realized_return",
            "realized_volatility",
            "max_drawdown",
            "hit",
            "forecast_error",
            "evaluated_at",
            "thesis_id",
            "scope_level",
            "target_id",
            "title",
            "summary",
            "thesis_evidence_hard",
            "thesis_evidence_soft",
        ],
    )
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    rows = repo.read_expected_vs_realized(horizon="1M", limit=25)

    sql, params = cursor.executed[0]
    assert "FROM forecast_records fr" in sql
    assert "LEFT JOIN realization_records rr ON rr.forecast_id = fr.id" in sql
    assert params == ("1M", 25)
    assert rows[0]["forecast_id"] == 7
    assert rows[0]["realization_id"] == 99
    assert rows[0]["forecast_evidence_hard"][0]["source"] == "fred"
    assert rows[0]["thesis_evidence_soft"][0]["source"] == "news"

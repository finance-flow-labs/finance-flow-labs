from datetime import datetime, timezone
import importlib

contracts = importlib.import_module("src.research.contracts")
postgres_repository = importlib.import_module("src.ingestion.postgres_repository")

NormalizedSeriesPoint = contracts.NormalizedSeriesPoint
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


def test_postgres_repository_writes_macro_series_points():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    written = repo.write_macro_series_points(
        [
            NormalizedSeriesPoint(
                source="fred",
                entity_id="CPIAUCSL",
                metric_key="CPIAUCSL",
                as_of=datetime(2024, 1, 1, tzinfo=timezone.utc),
                available_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
                value=3.2,
                lineage_id="lin-1",
            )
        ]
    )

    assert written == 1
    assert "INSERT INTO macro_series_points" in cursor.executed[0][0]
    assert conn.committed is True


def test_postgres_repository_reads_macro_series_points():
    cursor = FakeCursor(
        fetch_rows=[
            (
                "fred",
                "CPIAUCSL",
                "CPIAUCSL",
                "2024-01-01T00:00:00+00:00",
                "2024-01-02T00:00:00+00:00",
                3.2,
                "lin-1",
            )
        ],
        columns=[
            "source",
            "entity_id",
            "metric_key",
            "as_of",
            "available_at",
            "value",
            "lineage_id",
        ],
    )
    conn = FakeConnection(cursor)
    repo = PostgresRepository(connection_factory=lambda: conn)

    rows = repo.read_macro_series_points(metric_key="CPIAUCSL", limit=20)

    assert "FROM macro_series_points" in cursor.executed[0][0]
    assert rows[0]["metric_key"] == "CPIAUCSL"

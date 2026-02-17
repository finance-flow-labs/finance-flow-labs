from datetime import datetime, timezone
import importlib


filter_point_in_time = importlib.import_module(
    "src.ingestion.pit_query"
).filter_point_in_time


def test_pit_query_enforces_available_at_cutoff():
    decision_time = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
    rows = [
        {
            "entity_id": "AAA",
            "available_at": datetime(2026, 1, 9, 12, 0, 0, tzinfo=timezone.utc),
        },
        {
            "entity_id": "AAA",
            "available_at": datetime(2026, 1, 11, 12, 0, 0, tzinfo=timezone.utc),
        },
    ]

    result = filter_point_in_time(rows, decision_time)
    assert len(result) == 1


def test_pit_query_is_deterministically_ordered():
    decision_time = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
    rows = [
        {
            "entity_id": "BBB",
            "available_at": datetime(2026, 1, 9, 12, 0, 0, tzinfo=timezone.utc),
        },
        {
            "entity_id": "AAA",
            "available_at": datetime(2026, 1, 9, 12, 0, 0, tzinfo=timezone.utc),
        },
    ]
    result = filter_point_in_time(rows, decision_time)
    assert [row["entity_id"] for row in result] == ["AAA", "BBB"]

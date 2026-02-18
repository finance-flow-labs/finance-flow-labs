from datetime import datetime, timezone
import importlib

normalization = importlib.import_module("src.research.normalization")


def test_normalize_fred_payload_maps_observations_sorted():
    points = normalization.normalize_payload(
        source="fred",
        payload={
            "payload": {
                "observations": [
                    {"date": "2024-02-01", "value": "3.2"},
                    {"date": "2024-01-01", "value": "3.1"},
                ]
            }
        },
        entity_id="CPIAUCSL",
        available_at=datetime(2026, 2, 18, tzinfo=timezone.utc),
        lineage_id="lin-1",
    )

    assert len(points) == 2
    assert [p.value for p in points] == [3.1, 3.2]
    assert points[0].metric_key == "CPIAUCSL"


def test_normalize_ecos_payload_skips_malformed_rows():
    points = normalization.normalize_payload(
        source="ecos",
        payload={
            "payload": {
                "StatisticSearch": {
                    "row": [
                        {"TIME": "202401", "DATA_VALUE": "100.1", "ITEM_NAME1": "KOR_BASE_RATE"},
                        {"TIME": "", "DATA_VALUE": "100.5", "ITEM_NAME1": "KOR_BASE_RATE"},
                        {"TIME": "202402", "DATA_VALUE": "NaN", "ITEM_NAME1": "KOR_BASE_RATE"},
                    ]
                }
            }
        },
        entity_id="722Y001",
        available_at=datetime(2026, 2, 18, tzinfo=timezone.utc),
        lineage_id="lin-2",
    )

    assert len(points) == 1
    assert points[0].metric_key == "KOR_BASE_RATE"
    assert points[0].value == 100.1


def test_normalize_payload_unsupported_source_returns_empty():
    points = normalization.normalize_payload(
        source="sec_edgar",
        payload={"payload": {}},
        entity_id="0000320193",
        available_at=datetime(2026, 2, 18, tzinfo=timezone.utc),
        lineage_id="lin-3",
    )

    assert points == []

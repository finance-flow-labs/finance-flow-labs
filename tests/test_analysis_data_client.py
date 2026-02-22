from src.analysis.data_client import CanonicalDataClient, detect_anomalies
from _pytest.monkeypatch import MonkeyPatch


def test_canonical_data_client_falls_back_without_db(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.delenv("ECOS_API_KEY", raising=False)

    client = CanonicalDataClient()
    rows = client.read_series("fred", "CPIAUCSL", limit=5)

    assert rows == []


def test_detect_anomalies_skips_non_numeric_values():
    rows: list[dict[str, object]] = [
        {"metric_value": "1"},
        {"metric_value": 2},
        {"metric_value": "3"},
        {"metric_value": "bad"},
        {"metric_value": 10},
    ]

    result = detect_anomalies(rows, window=3, threshold=0.1)

    assert result == []


def test_detect_anomalies_uses_string_numbers():
    rows: list[dict[str, object]] = [
        {"metric_value": "1"},
        {"metric_value": "2"},
        {"metric_value": 3},
        {"metric_value": 4},
        {"metric_value": 100},
    ]

    result = detect_anomalies(rows, window=3, threshold=2.5)

    assert len(result) == 1
    assert result[0]["metric_value"] == 100

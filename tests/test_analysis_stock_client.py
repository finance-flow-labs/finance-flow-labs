import pytest

from src.analysis.stock_client import FmpStockClient


def test_fmp_stock_client_reports_missing_key_as_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    client = FmpStockClient()

    snapshot = client.fetch_snapshot("GOOGL")

    assert snapshot["endpoint_family"] == "stable"
    assert snapshot["symbol"] == "GOOGL"
    assert snapshot["quote"] == {}
    assert snapshot["key_metrics"] == []
    assert snapshot["analyst_estimates"] == []
    assert snapshot["price_target_consensus"] == {}
    assert snapshot["price_target_summary"] == {}
    assert snapshot["price_targets"] == []
    assert any("FMP_API_KEY is not set" in err for err in snapshot["errors"])


def test_fmp_stock_client_fetch_snapshot_aggregates_valuation_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FmpStockClient(api_key="test-key")

    def fake_get(path: str, params: dict[str, str]):
        if path == "/stable/search-symbol":
            return [
                {
                    "symbol": "GOOGL",
                    "name": "Alphabet Inc.",
                    "exchange": "NASDAQ",
                    "exchangeFullName": "NASDAQ Global Select",
                    "type": "stock",
                    "currency": "USD",
                }
            ]
        if path == "/stable/quote":
            assert params["symbol"] == "GOOGL"
            return [{"symbol": "GOOGL", "price": 181.25, "marketCap": 1_000_000_000}]
        if path == "/stable/key-metrics":
            assert params["symbol"] == "GOOGL"
            return [{"date": "2025-12-31", "peRatio": 24.5, "pbRatio": 7.2}]
        if path == "/stable/analyst-estimates":
            assert params["symbol"] == "GOOGL"
            assert params["period"] == "annual"
            assert params["limit"] == "3"
            return [{"date": "2026-12-31", "epsAvg": 9.8}]
        if path == "/stable/price-target-consensus":
            return [{"symbol": "GOOGL", "targetConsensus": 210.0, "targetHigh": 250.0}]
        if path == "/stable/price-target-summary":
            return [{"symbol": "GOOGL", "allTimeAvgPriceTarget": 220.0}]
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(client, "_get", fake_get)

    snapshot = client.fetch_snapshot("Google", limit=3)

    assert snapshot["endpoint_family"] == "stable"
    assert snapshot["symbol"] == "GOOGL"
    assert snapshot["companies"][0]["name"] == "Alphabet Inc."
    assert snapshot["quote"]["price"] == 181.25
    assert snapshot["key_metrics"][0]["peRatio"] == 24.5
    assert snapshot["analyst_estimates"][0]["epsAvg"] == 9.8
    assert snapshot["price_target_consensus"]["targetConsensus"] == 210.0
    assert snapshot["price_target_summary"]["allTimeAvgPriceTarget"] == 220.0
    assert snapshot["price_targets"][0]["allTimeAvgPriceTarget"] == 220.0
    assert snapshot["errors"] == []


def test_fmp_stock_client_collects_non_fatal_endpoint_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FmpStockClient(api_key="test-key")

    def fake_get(path: str, params: dict[str, str]):
        if path == "/stable/search-symbol":
            return []
        if path == "/stable/search-name":
            return []
        if path == "/stable/quote":
            raise ValueError("FMP HTTP 403 for /stable/quote")
        return []

    monkeypatch.setattr(client, "_get", fake_get)

    snapshot = client.fetch_snapshot("GOOGL", limit=2)

    assert snapshot["symbol"] == "GOOGL"
    assert snapshot["quote"] == {}
    assert any("quote" in err for err in snapshot["errors"])

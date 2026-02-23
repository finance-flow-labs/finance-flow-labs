import importlib

import pytest


performance_service = importlib.import_module("src.enduser.performance_service")


def test_build_performance_view_returns_empty_metrics_when_no_snapshots(monkeypatch):
    class EmptyRepository:
        def read_portfolio_snapshots(self, limit: int = 365):
            assert limit == 365
            return []

    monkeypatch.setattr(performance_service, "compute_benchmark_series", lambda repository, start_date, end_date: [])

    view = performance_service.build_performance_view(EmptyRepository())

    assert view["total_return_pct"] is None
    assert view["mdd_pct"] is None
    assert view["sharpe_ratio"] is None
    assert view["alpha_pct"] is None
    assert view["mdd_alert"] is False
    assert view["policy_mdd_limit_pct"] == pytest.approx(-30.0)
    assert view["us_weight_pct"] is None
    assert view["kr_weight_pct"] is None
    assert view["crypto_weight_pct"] is None
    assert view["other_weight_pct"] is None
    assert view["leverage_weight_pct"] is None
    assert view["leverage_cap_pct"] == pytest.approx(20.0)
    assert view["leverage_cap_breached"] is False
    assert view["nav_series"] == []
    assert view["benchmark_series"] == []


def test_build_performance_view_computes_total_return_mdd_sharpe_and_alpha(monkeypatch):
    class FakeRepository:
        def read_portfolio_snapshots(self, limit: int = 365):
            assert limit == 365
            # Repository returns newest-first; service should normalize to chronological order.
            return [
                {
                    "as_of": "2026-01-04",
                    "nav": 120,
                    "us_weight": 0.45,
                    "kr_weight": 0.25,
                    "crypto_weight": 0.20,
                    "leverage_weight": 0.10,
                },
                {
                    "as_of": "2026-01-03",
                    "nav": 100,
                    "us_weight": 0.45,
                    "kr_weight": 0.25,
                    "crypto_weight": 0.20,
                    "leverage_weight": 0.10,
                },
                {
                    "as_of": "2026-01-02",
                    "nav": 80,
                    "us_weight": 0.45,
                    "kr_weight": 0.25,
                    "crypto_weight": 0.20,
                    "leverage_weight": 0.10,
                },
                {
                    "as_of": "2026-01-01",
                    "nav": 100,
                    "us_weight": 0.45,
                    "kr_weight": 0.25,
                    "crypto_weight": 0.20,
                    "leverage_weight": 0.10,
                },
            ]

    benchmark_rows = [
        {"as_of": "2026-01-02", "benchmark_return": 0.01, "benchmark_nav": 1.01},
        {"as_of": "2026-01-03", "benchmark_return": 0.01, "benchmark_nav": 1.02},
        {"as_of": "2026-01-04", "benchmark_return": 0.01, "benchmark_nav": 1.03},
    ]

    monkeypatch.setattr(
        performance_service,
        "compute_benchmark_series",
        lambda repository, start_date, end_date: benchmark_rows,
    )

    view = performance_service.build_performance_view(FakeRepository())

    assert view["total_return_pct"] == pytest.approx(20.0)
    assert view["mdd_pct"] == pytest.approx(-20.0)
    assert view["mdd_alert"] is True
    assert view["sharpe_ratio"] is not None
    assert view["sharpe_ratio"] == pytest.approx(5.36, abs=0.01)
    # Alpha = 20.0% - 3.0%
    assert view["alpha_pct"] == pytest.approx(17.0)
    assert view["policy_mdd_limit_pct"] == pytest.approx(-30.0)
    assert view["mdd_policy_buffer_pp"] == pytest.approx(10.0)
    assert view["us_weight_pct"] == pytest.approx(45.0)
    assert view["kr_weight_pct"] == pytest.approx(25.0)
    assert view["crypto_weight_pct"] == pytest.approx(20.0)
    assert view["other_weight_pct"] == pytest.approx(10.0)
    assert view["leverage_weight_pct"] == pytest.approx(10.0)
    assert view["leverage_cap_pct"] == pytest.approx(20.0)
    assert view["leverage_cap_breached"] is False
    assert [row["as_of"] for row in view["nav_series"]] == [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
        "2026-01-04",
    ]


def test_build_performance_view_respects_mdd_alert_threshold_override(monkeypatch):
    class FakeRepository:
        def read_portfolio_snapshots(self, limit: int = 365):
            return [
                {"as_of": "2026-01-03", "nav": 95},
                {"as_of": "2026-01-02", "nav": 90},
                {"as_of": "2026-01-01", "nav": 100},
            ]

    monkeypatch.setattr(performance_service, "compute_benchmark_series", lambda repository, start_date, end_date: [])
    monkeypatch.setenv("MDD_ALERT_THRESHOLD", "-0.25")

    view = performance_service.build_performance_view(FakeRepository())

    assert view["mdd_pct"] == pytest.approx(-10.0)
    assert view["mdd_alert"] is False
    assert view["mdd_alert_threshold_pct"] == pytest.approx(-25.0)


def test_build_performance_view_respects_leverage_cap_override(monkeypatch):
    class FakeRepository:
        def read_portfolio_snapshots(self, limit: int = 365):
            return [
                {
                    "as_of": "2026-01-02",
                    "nav": 101,
                    "us_weight": 0.40,
                    "kr_weight": 0.25,
                    "crypto_weight": 0.20,
                    "leverage_weight": 0.18,
                },
                {
                    "as_of": "2026-01-01",
                    "nav": 100,
                    "us_weight": 0.40,
                    "kr_weight": 0.25,
                    "crypto_weight": 0.20,
                    "leverage_weight": 0.18,
                },
            ]

    monkeypatch.setattr(performance_service, "compute_benchmark_series", lambda repository, start_date, end_date: [])
    monkeypatch.setenv("LEVERAGE_CAP", "15")

    view = performance_service.build_performance_view(FakeRepository())

    assert view["leverage_weight_pct"] == pytest.approx(18.0)
    assert view["leverage_cap_pct"] == pytest.approx(15.0)
    assert view["leverage_cap_breached"] is True

import importlib


dashboard_app = importlib.import_module("src.dashboard.app")


def test_dashboard_app_module_loads():
    assert hasattr(dashboard_app, "build_operator_cards")


def test_dashboard_app_builds_cards_from_view_model():
    cards = dashboard_app.build_operator_cards(
        {
            "last_run_status": "success",
            "last_run_time": "2026-02-18T01:00:00Z",
            "counters": {
                "raw_events": 100,
                "canonical_events": 90,
                "quarantine_events": 10,
            },
            "learning_metrics": {
                "horizon": "1M",
                "realized_count": 10,
                "hit_rate": 0.6,
                "mean_abs_forecast_error": 0.025,
            },
            "recent_runs": [],
        }
    )

    assert cards["last_run_status"] == "success"
    assert cards["raw_events"] == 100
    assert cards["quarantine_events"] == 10
    assert cards["realized_count"] == 10
    assert cards["hit_rate_pct"] == "60.0%"
    assert cards["mae_pct"] == "2.50%"

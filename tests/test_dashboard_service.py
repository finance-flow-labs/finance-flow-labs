import importlib


dashboard_service = importlib.import_module("src.ingestion.dashboard_service")
build_dashboard_view = dashboard_service.build_dashboard_view


class FakeDashboardRepo:
    def read_latest_runs(self, limit=20):
        return [
            {"run_id": "run-2", "status": "success", "finished_at": "2026-02-18T01:00:00Z"},
            {"run_id": "run-1", "status": "quarantine", "finished_at": "2026-02-18T00:00:00Z"},
        ]

    def read_status_counters(self):
        return {"raw_events": 100, "canonical_events": 90, "quarantine_events": 10}

    def read_learning_metrics(self, horizon="1M"):
        return {
            "horizon": horizon,
            "forecast_count": 20,
            "realized_count": 12,
            "realization_coverage": 0.6,
            "hit_rate": 0.58,
            "mean_abs_forecast_error": 0.031,
        }

    def read_forecast_error_category_stats(self, horizon="1M", limit=5):
        return [
            {
                "category": "macro_miss",
                "attribution_count": 2,
                "mean_contribution": -0.021,
                "mean_abs_contribution": 0.021,
            },
            {
                "category": "valuation_miss",
                "attribution_count": 1,
                "mean_contribution": -0.008,
                "mean_abs_contribution": 0.008,
            },
        ]

    def read_forecast_error_attributions(self, horizon="1M", limit=200):
        return [
            {"category": "macro_miss", "evidence_hard": [{"source": "FRED"}], "evidence_soft": [{"note": "regime"}]},
            {"category": "macro_miss", "evidence_hard": [{"metric": "CPI"}], "evidence_soft": []},
            {"category": "valuation_miss", "evidence_hard": [], "evidence_soft": [{"note": "narrative"}]},
            {"category": "unknown", "evidence_hard": [], "evidence_soft": []},
        ]


def test_dashboard_service_builds_operator_view_model():
    view = build_dashboard_view(FakeDashboardRepo())

    assert view["last_run_status"] == "success"
    assert view["last_run_time"] == "2026-02-18T01:00:00Z"
    assert view["counters"]["raw_events"] == 100
    assert view["learning_metrics"]["horizon"] == "1M"
    assert view["learning_metrics"]["hit_rate"] == 0.58
    assert view["attribution_summary"]["total"] == 4
    assert view["attribution_summary"]["top_category"] == "macro_miss"
    assert view["attribution_summary"]["top_count"] == 2
    assert len(view["attribution_summary"]["top_categories"]) == 2
    assert view["attribution_summary"]["top_categories"][0]["mean_abs_contribution"] == 0.021
    assert view["attribution_summary"]["hard_evidence_coverage"] == 0.5
    assert view["attribution_summary"]["hard_evidence_traceability_coverage"] == 0.25
    assert view["attribution_summary"]["soft_evidence_coverage"] == 0.5
    assert view["attribution_summary"]["evidence_gap_count"] == 1
    assert view["attribution_summary"]["evidence_gap_coverage"] == 0.25
    assert len(view["recent_runs"]) == 2

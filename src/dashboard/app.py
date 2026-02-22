import os
import importlib
from collections.abc import Mapping


def build_operator_cards(view: Mapping[str, object]) -> dict[str, object]:
    def to_int(value: object) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            return int(value)
        return 0

    counters = view.get("counters", {})
    if isinstance(counters, Mapping):
        raw_events = to_int(counters.get("raw_events", 0))
        canonical_events = to_int(counters.get("canonical_events", 0))
        quarantine_events = to_int(counters.get("quarantine_events", 0))
    else:
        raw_events = 0
        canonical_events = 0
        quarantine_events = 0

    learning = view.get("learning_metrics", {})
    if isinstance(learning, Mapping):
        forecast_count = to_int(learning.get("forecast_count", 0))
        realized_count = to_int(learning.get("realized_count", 0))
        realization_coverage = learning.get("realization_coverage")
        hit_rate = learning.get("hit_rate")
        mae = learning.get("mean_abs_forecast_error")
    else:
        forecast_count = 0
        realized_count = 0
        realization_coverage = None
        hit_rate = None
        mae = None

    attribution_summary = view.get("attribution_summary", {})
    if isinstance(attribution_summary, Mapping):
        attribution_total = to_int(attribution_summary.get("total", 0))
        top_category = str(attribution_summary.get("top_category", "n/a"))
        top_count = to_int(attribution_summary.get("top_count", 0))
    else:
        attribution_total = 0
        top_category = "n/a"
        top_count = 0

    coverage_pct = "n/a" if not isinstance(realization_coverage, (int, float)) else f"{realization_coverage * 100:.1f}%"
    hit_rate_pct = "n/a" if not isinstance(hit_rate, (int, float)) else f"{hit_rate * 100:.1f}%"
    mae_pct = "n/a" if not isinstance(mae, (int, float)) else f"{mae * 100:.2f}%"

    return {
        "last_run_status": str(view.get("last_run_status", "no-data")),
        "last_run_time": str(view.get("last_run_time", "")),
        "raw_events": raw_events,
        "canonical_events": canonical_events,
        "quarantine_events": quarantine_events,
        "forecast_count": forecast_count,
        "realized_count": realized_count,
        "coverage_pct": coverage_pct,
        "hit_rate_pct": hit_rate_pct,
        "mae_pct": mae_pct,
        "attribution_total": attribution_total,
        "attribution_top_category": top_category,
        "attribution_top_count": top_count,
    }


def load_dashboard_view(dsn: str) -> dict[str, object]:
    dashboard_service = importlib.import_module("src.ingestion.dashboard_service")
    postgres_repository = importlib.import_module("src.ingestion.postgres_repository")
    repository = postgres_repository.PostgresRepository(dsn=dsn)
    build_dashboard_view = dashboard_service.build_dashboard_view
    return build_dashboard_view(repository)


def run_streamlit_app(dsn: str) -> None:
    st = importlib.import_module("streamlit")

    view = load_dashboard_view(dsn)
    cards = build_operator_cards(view)

    st.set_page_config(page_title="Ingestion Operator Dashboard", layout="wide")
    st.title("Ingestion Operator Dashboard")
    st.caption("Manual update monitoring (cron separated)")

    c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11 = st.columns(11)
    c1.metric("Last Status", cards["last_run_status"], cards["last_run_time"])
    c2.metric("Raw", cards["raw_events"])
    c3.metric("Canonical", cards["canonical_events"])
    c4.metric("Quarantine", cards["quarantine_events"])
    c5.metric("1M Forecasts", cards["forecast_count"])
    c6.metric("1M Realized", cards["realized_count"])
    c7.metric("1M Coverage", cards["coverage_pct"])
    c8.metric("1M Hit Rate", cards["hit_rate_pct"])
    c9.metric("1M MAE", cards["mae_pct"])
    c10.metric("1M Attr", cards["attribution_total"])
    c11.metric("Top Attr", cards["attribution_top_category"], cards["attribution_top_count"])

    recent_runs = view.get("recent_runs", [])
    if isinstance(recent_runs, list) and recent_runs:
        st.subheader("Recent Runs")
        st.dataframe(recent_runs, use_container_width=True)
    else:
        st.info("No run history found.")


def main() -> None:
    dsn = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        raise ValueError("SUPABASE_DB_URL or DATABASE_URL is required")
    run_streamlit_app(dsn)


if __name__ == "__main__":
    main()

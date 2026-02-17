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

    return {
        "last_run_status": str(view.get("last_run_status", "no-data")),
        "last_run_time": str(view.get("last_run_time", "")),
        "raw_events": raw_events,
        "canonical_events": canonical_events,
        "quarantine_events": quarantine_events,
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

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Last Status", cards["last_run_status"])
    c2.metric("Raw", cards["raw_events"])
    c3.metric("Canonical", cards["canonical_events"])
    c4.metric("Quarantine", cards["quarantine_events"])
    c5.metric("Last Run Time", cards["last_run_time"])

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

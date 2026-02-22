import argparse
import importlib
import json
import os
import urllib.request
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Optional

from .adapters.ecos import EcosAdapter
from .adapters.fred import FredAdapter
from .adapters.opendart import OpenDartAdapter
from .adapters.sec_edgar import SecEdgarAdapter
from .http_client import HttpResponse, SimpleHttpClient
from .postgres_repository import PostgresRepository
from .quality_gate import BatchMetrics
from .repository import InMemoryRepository
from .source_registry import SourceDescriptor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ingestion")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_update = subparsers.add_parser("run-update")
    _ = run_update.add_argument("--source", required=True)
    _ = run_update.add_argument("--entity")

    expected_vs_realized = subparsers.add_parser("expected-vs-realized")
    _ = expected_vs_realized.add_argument("--horizon", default="1M")
    _ = expected_vs_realized.add_argument("--limit", type=int, default=50)

    forecast_error_attributions = subparsers.add_parser("forecast-error-attributions")
    _ = forecast_error_attributions.add_argument("--horizon", default="1M")
    _ = forecast_error_attributions.add_argument("--limit", type=int, default=50)

    return parser


def _urllib_transport(method: str, url: str, headers: Mapping[str, str]) -> HttpResponse:
    request = urllib.request.Request(url=url, method=method, headers=dict(headers))
    with urllib.request.urlopen(request, timeout=30) as response:
        return HttpResponse(
            status_code=response.status,
            body=response.read(),
            headers=dict(response.headers.items()),
        )


def _collect_payload(source: str, entity: Optional[str]) -> tuple[str, dict[str, object]]:
    client = SimpleHttpClient(transport=_urllib_transport, max_retries=2)

    if source == "sec_edgar":
        cik = entity or os.getenv("SEC_CIK", "0000320193")
        user_agent = os.getenv("SEC_USER_AGENT", "finanace-flow-labs/0.1 ops@example.com")
        payload = SecEdgarAdapter(client=client, user_agent=user_agent).fetch_company_facts(cik)
        return cik, payload

    if source == "fred":
        series_id = entity or os.getenv("FRED_SERIES_ID", "CPIAUCSL")
        api_key = os.getenv("FRED_API_KEY", "")
        payload = FredAdapter(client=client, api_key=api_key).fetch_series_observations(series_id)
        return series_id, payload

    if source == "opendart":
        corp_code = entity or os.getenv("DART_CORP_CODE", "00126380")
        api_key = os.getenv("DART_API_KEY", os.getenv("DART_CRTFC_KEY", ""))
        payload = OpenDartAdapter(client=client, api_key=api_key).fetch_company(corp_code)
        return corp_code, payload

    if source == "ecos":
        stat_code = entity or os.getenv("ECOS_STAT_CODE", "722Y001")
        api_key = os.getenv("ECOS_API_KEY", "")
        payload = EcosAdapter(client=client, api_key=api_key).fetch_statistic(stat_code)
        return stat_code, payload

    raise ValueError(f"unsupported source: {source}")


def run_update_command(source: str, entity: Optional[str] = None) -> dict[str, object]:
    manual_runner = importlib.import_module("src.ingestion.manual_runner")
    run_manual_update = manual_runner.run_manual_update
    entity_id, payload = _collect_payload(source, entity)

    dsn = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    run_history_repository = PostgresRepository(dsn=dsn) if dsn else None
    data_repository = PostgresRepository(dsn=dsn) if dsn else InMemoryRepository()

    now = datetime.now(timezone.utc)
    summary = run_manual_update(
        source=SourceDescriptor(
            name=source,
            utility=5,
            reliability=4,
            legal=4,
            cost=3,
            maintenance=3,
        ),
        metrics=BatchMetrics(
            freshness=True,
            completeness=True,
            schema_drift=False,
            license_ok=True,
        ),
        idempotency_key=f"{source}|{entity_id}|{now.date().isoformat()}|manual",
        payload=payload,
        rows=[{"entity_id": entity_id, "available_at": now}],
        decision_time=now,
        repository=data_repository,
        run_history_repository=run_history_repository,
    )
    return summary


def read_expected_vs_realized_command(horizon: str = "1M", limit: int = 50) -> list[dict[str, object]]:
    dsn = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        raise ValueError("SUPABASE_DB_URL or DATABASE_URL is required")

    repository = PostgresRepository(dsn=dsn)
    return repository.read_expected_vs_realized(horizon=horizon, limit=limit)


def read_forecast_error_attributions_command(
    horizon: str = "1M", limit: int = 50
) -> list[dict[str, object]]:
    dsn = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        raise ValueError("SUPABASE_DB_URL or DATABASE_URL is required")

    repository = PostgresRepository(dsn=dsn)
    return repository.read_forecast_error_attributions(horizon=horizon, limit=limit)


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run-update":
        summary = run_update_command(args.source, args.entity)
        print(json.dumps(summary))
        return 0

    if args.command == "expected-vs-realized":
        rows = read_expected_vs_realized_command(horizon=args.horizon, limit=args.limit)
        print(json.dumps(rows, default=str))
        return 0

    if args.command == "forecast-error-attributions":
        rows = read_forecast_error_attributions_command(horizon=args.horizon, limit=args.limit)
        print(json.dumps(rows, default=str))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

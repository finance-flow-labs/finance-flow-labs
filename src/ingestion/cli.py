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

    forecast_error_category_stats = subparsers.add_parser("forecast-error-category-stats")
    _ = forecast_error_category_stats.add_argument("--horizon", default="1M")
    _ = forecast_error_category_stats.add_argument("--limit", type=int, default=20)

    forecast_record_create = subparsers.add_parser("forecast-record-create")
    _ = forecast_record_create.add_argument("--thesis-id", required=True)
    _ = forecast_record_create.add_argument("--horizon", required=True, choices=["1W", "1M", "3M"])
    _ = forecast_record_create.add_argument("--expected-return-low", required=True, type=float)
    _ = forecast_record_create.add_argument("--expected-return-high", required=True, type=float)
    _ = forecast_record_create.add_argument("--expected-volatility", type=float)
    _ = forecast_record_create.add_argument("--expected-drawdown", type=float)
    _ = forecast_record_create.add_argument("--confidence", required=True, type=float)
    _ = forecast_record_create.add_argument("--key-drivers-json", default="[]")
    _ = forecast_record_create.add_argument("--evidence-hard-json", required=True)
    _ = forecast_record_create.add_argument("--evidence-soft-json", default="[]")
    _ = forecast_record_create.add_argument("--as-of", required=True)

    streamlit_access_check = subparsers.add_parser("streamlit-access-check")
    _ = streamlit_access_check.add_argument("--url", required=True)
    _ = streamlit_access_check.add_argument("--timeout-seconds", type=float, default=15)
    _ = streamlit_access_check.add_argument("--attempts", type=int, default=3)
    _ = streamlit_access_check.add_argument("--backoff-seconds", type=float, default=0.5)

    deploy_access_gate = subparsers.add_parser("deploy-access-gate")
    _ = deploy_access_gate.add_argument("--url", required=True)
    _ = deploy_access_gate.add_argument("--mode", choices=["public", "restricted"])
    _ = deploy_access_gate.add_argument("--restricted-login-path")
    _ = deploy_access_gate.add_argument("--timeout-seconds", type=float, default=15)
    _ = deploy_access_gate.add_argument("--attempts", type=int, default=3)
    _ = deploy_access_gate.add_argument("--backoff-seconds", type=float, default=0.5)

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


def _parse_json_array(raw: str, field_name: str) -> list[object]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON: {exc.msg}") from exc
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array")
    return value


def _parse_iso_datetime(raw: str, field_name: str) -> datetime:
    normalized = raw.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601 datetime") from exc
    if dt.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone offset (e.g. +00:00)")
    return dt


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


def read_forecast_error_category_stats_command(
    horizon: str = "1M", limit: int = 20
) -> list[dict[str, object]]:
    dsn = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        raise ValueError("SUPABASE_DB_URL or DATABASE_URL is required")

    repository = PostgresRepository(dsn=dsn)
    return repository.read_forecast_error_category_stats(horizon=horizon, limit=limit)


def run_streamlit_access_check_command(
    url: str,
    timeout_seconds: float = 15,
    attempts: int = 3,
    backoff_seconds: float = 0.5,
) -> dict[str, object]:
    streamlit_access = importlib.import_module("src.ingestion.streamlit_access")
    check_streamlit_access = streamlit_access.check_streamlit_access
    result = check_streamlit_access(
        url=url,
        timeout_seconds=timeout_seconds,
        attempts=attempts,
        backoff_seconds=backoff_seconds,
    )
    return result.to_dict()


def run_deploy_access_gate_command(
    url: str,
    mode: str | None = None,
    restricted_login_path: str | None = None,
    timeout_seconds: float = 15,
    attempts: int = 3,
    backoff_seconds: float = 0.5,
) -> dict[str, object]:
    deploy_policy = importlib.import_module("src.ingestion.deploy_access_policy")

    effective_mode = mode or os.getenv("DEPLOY_ACCESS_MODE", "public")
    effective_restricted_login_path = restricted_login_path or os.getenv("DEPLOY_RESTRICTED_LOGIN_PATH")

    access_result = run_streamlit_access_check_command(
        url=url,
        timeout_seconds=timeout_seconds,
        attempts=attempts,
        backoff_seconds=backoff_seconds,
    )
    decision = deploy_policy.evaluate_deploy_access(
        access_result,
        mode=effective_mode,
        restricted_login_path=effective_restricted_login_path,
    )

    return {
        "url": url,
        "deploy_access_mode": deploy_policy.normalize_access_mode(effective_mode),
        "restricted_login_path": effective_restricted_login_path,
        "access_check": access_result,
        "gate": decision.to_dict(),
    }


def create_forecast_record_command(
    thesis_id: str,
    horizon: str,
    expected_return_low: float,
    expected_return_high: float,
    confidence: float,
    as_of: str,
    key_drivers_json: str,
    evidence_hard_json: str,
    evidence_soft_json: str = "[]",
    expected_volatility: Optional[float] = None,
    expected_drawdown: Optional[float] = None,
) -> dict[str, object]:
    dsn = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        raise ValueError("SUPABASE_DB_URL or DATABASE_URL is required")

    if expected_return_low > expected_return_high:
        raise ValueError("expected_return_low must be <= expected_return_high")
    if not (0 <= confidence <= 1):
        raise ValueError("confidence must be between 0 and 1")

    key_drivers = _parse_json_array(key_drivers_json, "key_drivers_json")
    evidence_hard = _parse_json_array(evidence_hard_json, "evidence_hard_json")
    evidence_soft = _parse_json_array(evidence_soft_json, "evidence_soft_json")

    if not evidence_hard:
        raise ValueError("evidence_hard_json must be a non-empty JSON array")

    payload = {
        "thesis_id": thesis_id,
        "horizon": horizon,
        "expected_return_low": expected_return_low,
        "expected_return_high": expected_return_high,
        "expected_volatility": expected_volatility,
        "expected_drawdown": expected_drawdown,
        "confidence": confidence,
        "key_drivers": key_drivers,
        "evidence_hard": evidence_hard,
        "evidence_soft": evidence_soft,
        "as_of": _parse_iso_datetime(as_of, "as_of"),
    }

    repository = PostgresRepository(dsn=dsn)
    forecast_id, deduplicated = repository.write_forecast_record_idempotent(payload)
    return {
        "forecast_id": forecast_id,
        "deduplicated": deduplicated,
        "thesis_id": thesis_id,
        "horizon": horizon,
    }


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

    if args.command == "forecast-error-category-stats":
        rows = read_forecast_error_category_stats_command(horizon=args.horizon, limit=args.limit)
        print(json.dumps(rows, default=str))
        return 0

    if args.command == "forecast-record-create":
        row = create_forecast_record_command(
            thesis_id=args.thesis_id,
            horizon=args.horizon,
            expected_return_low=args.expected_return_low,
            expected_return_high=args.expected_return_high,
            expected_volatility=args.expected_volatility,
            expected_drawdown=args.expected_drawdown,
            confidence=args.confidence,
            key_drivers_json=args.key_drivers_json,
            evidence_hard_json=args.evidence_hard_json,
            evidence_soft_json=args.evidence_soft_json,
            as_of=args.as_of,
        )
        print(json.dumps(row, default=str))
        return 0

    if args.command == "streamlit-access-check":
        result = run_streamlit_access_check_command(
            url=args.url,
            timeout_seconds=args.timeout_seconds,
            attempts=args.attempts,
            backoff_seconds=args.backoff_seconds,
        )
        print(json.dumps(result, default=str))
        return 0 if bool(result.get("ok")) else 2

    if args.command == "deploy-access-gate":
        result = run_deploy_access_gate_command(
            url=args.url,
            mode=args.mode,
            restricted_login_path=args.restricted_login_path,
            timeout_seconds=args.timeout_seconds,
            attempts=args.attempts,
            backoff_seconds=args.backoff_seconds,
        )
        print(json.dumps(result, default=str))
        gate = result.get("gate") if isinstance(result, dict) else None
        gate_ok = bool(gate.get("ok")) if isinstance(gate, dict) else False
        return 0 if gate_ok else 2

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

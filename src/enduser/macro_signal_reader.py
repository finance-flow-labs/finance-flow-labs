from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from src.ingestion.postgres_repository import PostgresRepository


RepositoryFactory = Callable[[str], Any]


def _parse_as_of(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value.strip():
        raw = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def read_latest_macro_regime_signal(
    dsn: str,
    *,
    freshness_days: int = 7,
    repository_factory: RepositoryFactory = PostgresRepository,
) -> dict[str, Any]:
    try:
        repository = repository_factory(dsn)
        rows = repository.read_latest_macro_analysis(limit=1)
    except Exception as exc:  # pragma: no cover - defensive UI boundary
        return {
            "status": "error",
            "reason": "error",
            "message": f"Failed to read macro regime signal: {exc}",
        }

    if not rows:
        return {
            "status": "missing",
            "reason": "missing",
            "message": "No macro regime record found in DB.",
        }

    row = rows[0]
    regime = row.get("regime")
    as_of = row.get("as_of")
    confidence = row.get("confidence")

    if not regime or as_of is None:
        return {
            "status": "error",
            "reason": "malformed",
            "message": "Latest macro regime row is malformed (missing regime/as_of).",
            "raw": row,
        }

    as_of_dt = _parse_as_of(as_of)
    stale = as_of_dt is None or as_of_dt < datetime.now(timezone.utc) - timedelta(days=freshness_days)

    payload: dict[str, Any] = {
        "status": "stale" if stale else "ok",
        "reason": "stale" if stale else "ok",
        "regime": regime,
        "confidence": confidence,
        "drivers": row.get("reason_codes") or [],
        "as_of": as_of,
        "lineage_id": row.get("run_id"),
        "evidence_hard": row.get("evidence_hard") or [],
        "evidence_soft": row.get("evidence_soft") or [],
    }

    if stale:
        payload["message"] = f"Latest macro regime signal is stale (> {freshness_days} days)."

    return payload

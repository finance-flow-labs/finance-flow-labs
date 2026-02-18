from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Optional


def _parse_datetime(value: object) -> Optional[datetime]:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    if not isinstance(value, str) or not value:
        return None

    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _to_float(value: object) -> Optional[float]:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _metric_polarity(metric_key: str) -> int:
    normalized = metric_key.upper()

    negative_on_up = (
        "CPI",
        "PPI",
        "INFLATION",
        "UNRATE",
        "RATE",
        "YIELD",
    )
    positive_on_up = (
        "GDP",
        "PMI",
        "PRODUCTION",
        "PAYROLL",
        "EMPLOYMENT",
        "SALES",
    )

    if any(token in normalized for token in negative_on_up):
        return -1
    if any(token in normalized for token in positive_on_up):
        return 1
    return 1


def prepare_metric_series(
    rows: Sequence[Mapping[str, object]],
    as_of: Optional[datetime] = None,
    limit: int = 120,
) -> list[float]:
    filtered: list[tuple[datetime, float]] = []
    effective_as_of = as_of
    if effective_as_of is not None and effective_as_of.tzinfo is None:
        effective_as_of = effective_as_of.replace(tzinfo=timezone.utc)

    for row in rows:
        value = _to_float(row.get("value"))
        at = _parse_datetime(row.get("as_of"))
        if value is None or at is None:
            continue
        if effective_as_of is not None and at > effective_as_of:
            continue
        filtered.append((at, value))

    filtered.sort(key=lambda item: item[0])
    values = [item[1] for item in filtered]

    if limit > 0:
        return values[-limit:]
    return values


def analyze_quant_regime(
    series_by_metric: Mapping[str, Sequence[float]],
) -> dict[str, object]:
    reason_codes: list[str] = []
    risk_flags: list[str] = []
    triggers: list[str] = []
    score = 0.0
    valid_signals = 0

    for metric_key in sorted(series_by_metric.keys()):
        values = list(series_by_metric.get(metric_key, []))
        if len(values) < 2:
            risk_flags.append(f"insufficient_data:{metric_key}")
            triggers.append(f"refresh:{metric_key}")
            continue

        latest = values[-1]
        previous = values[-2]
        delta = latest - previous

        if delta > 1e-12:
            direction = "up"
            direction_sign = 1.0
        elif delta < -1e-12:
            direction = "down"
            direction_sign = -1.0
        else:
            direction = "flat"
            direction_sign = 0.0

        polarity = float(_metric_polarity(metric_key))
        contribution = polarity * direction_sign
        score += contribution
        valid_signals += 1

        reason_codes.append(f"{metric_key}:{direction}")
        triggers.append(f"next_release:{metric_key}")

    if valid_signals == 0:
        regime = "neutral"
        confidence = 0.0
        risk_flags.append("no_macro_series_data")
    else:
        normalized_score = score / valid_signals
        if normalized_score >= 0.34:
            regime = "expansion"
        elif normalized_score <= -0.34:
            regime = "slowdown"
        else:
            regime = "neutral"

        base_confidence = abs(normalized_score)
        coverage_boost = valid_signals / max(1, len(series_by_metric))
        confidence = min(0.95, round(base_confidence * 0.7 + coverage_boost * 0.3, 4))

    if not reason_codes:
        reason_codes.append("insufficient_signals")

    # Deterministic ordering for stable snapshots.
    return {
        "regime": regime,
        "confidence": confidence,
        "score": score,
        "valid_signals": valid_signals,
        "reason_codes": sorted(set(reason_codes)),
        "risk_flags": sorted(set(risk_flags)),
        "triggers": sorted(set(triggers)),
    }

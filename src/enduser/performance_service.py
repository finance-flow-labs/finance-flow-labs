from __future__ import annotations

import math
import os
from datetime import date, datetime
from statistics import stdev
from typing import Any

from src.enduser.benchmark_service import compute_benchmark_series


DEFAULT_MDD_ALERT_THRESHOLD = -0.20
DEFAULT_POLICY_MDD_LIMIT = -0.30
DEFAULT_LEVERAGE_CAP = 0.20


def _parse_as_of(raw: object) -> date | None:
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw

    text = str(raw).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


def _to_float(raw: object) -> float | None:
    try:
        if raw is None:
            return None
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return value


def _to_weight_pct(raw: object) -> float | None:
    value = _to_float(raw)
    if value is None or value < 0:
        return None

    # DB usually stores weights in [0, 1], but tolerate percent input for robustness.
    if value <= 1.0:
        return value * 100.0
    if value <= 100.0:
        return value
    return None


def _load_negative_ratio(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default

    try:
        parsed = float(raw)
    except ValueError:
        return default

    if parsed > 0:
        parsed = -parsed

    if parsed < -1.0:
        parsed = parsed / 100.0

    if parsed > 0 or parsed < -1.0:
        return default

    return parsed


def _load_mdd_alert_threshold() -> float:
    return _load_negative_ratio("MDD_ALERT_THRESHOLD", DEFAULT_MDD_ALERT_THRESHOLD)


def _load_policy_mdd_limit() -> float:
    return _load_negative_ratio("MDD_POLICY_LIMIT", DEFAULT_POLICY_MDD_LIMIT)


def _load_leverage_cap() -> float:
    raw = os.getenv("LEVERAGE_CAP")
    if raw is None or raw.strip() == "":
        return DEFAULT_LEVERAGE_CAP

    try:
        parsed = float(raw)
    except ValueError:
        return DEFAULT_LEVERAGE_CAP

    if parsed < 0:
        return DEFAULT_LEVERAGE_CAP

    if parsed > 1.0:
        parsed = parsed / 100.0

    if parsed < 0 or parsed > 1.0:
        return DEFAULT_LEVERAGE_CAP

    return parsed


def _compute_mdd(nav_points: list[tuple[date, float]]) -> float | None:
    if not nav_points:
        return None

    peak = nav_points[0][1]
    if peak <= 0:
        return None

    mdd = 0.0
    for _, nav in nav_points:
        if nav <= 0:
            continue
        if nav > peak:
            peak = nav
            continue
        drawdown = (nav / peak) - 1.0
        if drawdown < mdd:
            mdd = drawdown
    return mdd


def _compute_daily_returns(nav_points: list[tuple[date, float]]) -> list[float]:
    returns: list[float] = []
    for idx in range(1, len(nav_points)):
        prev_nav = nav_points[idx - 1][1]
        nav = nav_points[idx][1]
        if prev_nav <= 0:
            continue
        returns.append((nav / prev_nav) - 1.0)
    return returns


def _compute_sharpe_ratio(daily_returns: list[float]) -> float | None:
    if len(daily_returns) < 2:
        return None

    mean_return = sum(daily_returns) / len(daily_returns)
    volatility = stdev(daily_returns)
    if volatility == 0:
        return None

    return (mean_return / volatility) * math.sqrt(252)


def build_performance_view(repository: object, limit: int = 365) -> dict[str, Any]:
    rows = repository.read_portfolio_snapshots(limit=limit) if hasattr(repository, "read_portfolio_snapshots") else []

    snapshots: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue

        as_of = _parse_as_of(row.get("as_of"))
        nav = _to_float(row.get("nav"))
        if as_of is None or nav is None or nav <= 0:
            continue

        snapshots.append(
            {
                "as_of": as_of,
                "nav": nav,
                "us_weight_pct": _to_weight_pct(row.get("us_weight")),
                "kr_weight_pct": _to_weight_pct(row.get("kr_weight")),
                "crypto_weight_pct": _to_weight_pct(row.get("crypto_weight")),
                "leverage_weight_pct": _to_weight_pct(row.get("leverage_weight")),
            }
        )

    snapshots.sort(key=lambda item: item["as_of"])
    nav_points: list[tuple[date, float]] = [(item["as_of"], item["nav"]) for item in snapshots]

    nav_series: list[dict[str, Any]] = []
    for idx, (as_of, nav) in enumerate(nav_points):
        if idx == 0:
            daily_return = None
        else:
            prev_nav = nav_points[idx - 1][1]
            daily_return = (nav / prev_nav) - 1.0 if prev_nav > 0 else None
        nav_series.append(
            {
                "as_of": as_of.isoformat(),
                "nav": nav,
                "daily_return": daily_return,
            }
        )

    total_return: float | None = None
    if len(nav_points) >= 2 and nav_points[0][1] > 0:
        total_return = (nav_points[-1][1] / nav_points[0][1]) - 1.0

    mdd = _compute_mdd(nav_points)
    sharpe = _compute_sharpe_ratio(_compute_daily_returns(nav_points))

    benchmark_series: list[dict[str, Any]] = []
    benchmark_total_return: float | None = None
    if nav_points:
        benchmark_series = compute_benchmark_series(
            repository,
            start_date=nav_points[0][0].isoformat(),
            end_date=nav_points[-1][0].isoformat(),
        )
        if benchmark_series:
            last_nav = _to_float(benchmark_series[-1].get("benchmark_nav"))
            if last_nav is not None:
                benchmark_total_return = last_nav - 1.0

    alpha: float | None = None
    if total_return is not None and benchmark_total_return is not None:
        alpha = total_return - benchmark_total_return

    mdd_alert_threshold = _load_mdd_alert_threshold()
    policy_mdd_limit = _load_policy_mdd_limit()
    leverage_cap = _load_leverage_cap()

    # Floating-point safety for threshold edge values (e.g. -0.2 exactly).
    mdd_alert = bool(mdd is not None and mdd <= (mdd_alert_threshold + 1e-9))

    latest_snapshot = snapshots[-1] if snapshots else None
    us_weight_pct = latest_snapshot.get("us_weight_pct") if latest_snapshot else None
    kr_weight_pct = latest_snapshot.get("kr_weight_pct") if latest_snapshot else None
    crypto_weight_pct = latest_snapshot.get("crypto_weight_pct") if latest_snapshot else None
    leverage_weight_pct = latest_snapshot.get("leverage_weight_pct") if latest_snapshot else None

    known_total = sum(v for v in [us_weight_pct, kr_weight_pct, crypto_weight_pct] if v is not None)
    other_weight_pct = (
        max(0.0, 100.0 - known_total)
        if any(v is not None for v in [us_weight_pct, kr_weight_pct, crypto_weight_pct])
        else None
    )

    mdd_pct = mdd * 100 if mdd is not None else None
    policy_mdd_limit_pct = policy_mdd_limit * 100
    mdd_policy_buffer_pp = max(0.0, mdd_pct - policy_mdd_limit_pct) if mdd_pct is not None else None

    leverage_cap_pct = leverage_cap * 100
    leverage_cap_breached = bool(
        leverage_weight_pct is not None and leverage_weight_pct > (leverage_cap_pct + 1e-9)
    )

    return {
        "total_return_pct": total_return * 100 if total_return is not None else None,
        "mdd_pct": mdd_pct,
        "sharpe_ratio": sharpe,
        "alpha_pct": alpha * 100 if alpha is not None else None,
        "mdd_alert": mdd_alert,
        "mdd_alert_threshold_pct": mdd_alert_threshold * 100,
        "policy_mdd_limit_pct": policy_mdd_limit_pct,
        "mdd_policy_buffer_pp": mdd_policy_buffer_pp,
        "us_weight_pct": us_weight_pct,
        "kr_weight_pct": kr_weight_pct,
        "crypto_weight_pct": crypto_weight_pct,
        "other_weight_pct": other_weight_pct,
        "leverage_weight_pct": leverage_weight_pct,
        "leverage_cap_pct": leverage_cap_pct,
        "leverage_cap_breached": leverage_cap_breached,
        "nav_series": nav_series,
        "benchmark_series": benchmark_series,
    }

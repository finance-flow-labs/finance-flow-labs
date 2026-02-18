import os
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Optional, Protocol
from uuid import uuid4

from .agent_views import (
    build_risk_view,
    build_strategist_view,
    synthesize_macro_analysis,
)
from .macro_analysis import analyze_quant_regime, prepare_metric_series
from . import opencode_runner


class MacroAnalysisRepositoryProtocol(Protocol):
    def read_macro_series_points(
        self,
        metric_key: str,
        limit: int = 100,
    ) -> list[dict[str, object]]: ...

    def write_macro_analysis_result(self, result: Mapping[str, object]) -> None: ...


def _resolve_metric_keys(metric_keys: Optional[Sequence[str]]) -> list[str]:
    from_argument = [key.strip() for key in metric_keys or [] if key.strip()]
    if from_argument:
        return sorted(set(from_argument))

    from_env_raw = os.getenv("MACRO_METRIC_KEYS", "").strip()
    if from_env_raw:
        from_env = [part.strip() for part in from_env_raw.split(",") if part.strip()]
        if from_env:
            return sorted(set(from_env))

    return ["CPIAUCSL"]


def _normalize_as_of(as_of: Optional[datetime]) -> datetime:
    effective = as_of or datetime.now(timezone.utc)
    if effective.tzinfo is None:
        return effective.replace(tzinfo=timezone.utc)
    return effective


def _resolve_analysis_engine(analysis_engine: str) -> str:
    normalized = analysis_engine.strip().lower()
    if normalized in {"opencode", "fallback"}:
        return normalized
    raise ValueError("analysis_engine must be one of: opencode, fallback")


def _resolve_model_name(
    strategist_result: Mapping[str, object],
    risk_result: Mapping[str, object],
) -> str:
    strategist_model = strategist_result.get("model")
    risk_model = risk_result.get("model")

    strategist_name = strategist_model.strip() if isinstance(strategist_model, str) else ""
    risk_name = risk_model.strip() if isinstance(risk_model, str) else ""

    if strategist_name and strategist_name == risk_name:
        return strategist_name
    if strategist_name:
        return strategist_name
    if risk_name:
        return risk_name
    return "deterministic-fallback"


def _extract_view(
    result: Mapping[str, object],
    *,
    fallback: dict[str, object],
) -> dict[str, object]:
    view = result.get("view")
    if isinstance(view, Mapping):
        return dict(view)
    return fallback


def run_macro_analysis_flow(
    repository: MacroAnalysisRepositoryProtocol,
    metric_keys: Optional[Sequence[str]] = None,
    as_of: Optional[datetime] = None,
    limit: int = 120,
    analysis_engine: str = "opencode",
    run_id: Optional[str] = None,
) -> dict[str, object]:
    resolved_metric_keys = _resolve_metric_keys(metric_keys)
    effective_as_of = _normalize_as_of(as_of)

    series_by_metric: dict[str, list[float]] = {}
    for metric_key in resolved_metric_keys:
        rows = repository.read_macro_series_points(metric_key=metric_key, limit=limit)
        values = prepare_metric_series(rows=rows, as_of=effective_as_of, limit=limit)
        if values:
            series_by_metric[metric_key] = values

    quant_summary = analyze_quant_regime(series_by_metric)

    requested_engine = _resolve_analysis_engine(analysis_engine)
    if requested_engine == "opencode":
        strategist_result = opencode_runner.generate_strategist_view(quant_summary)
        risk_result = opencode_runner.generate_risk_view(quant_summary)
        strategist_view = _extract_view(
            strategist_result,
            fallback=build_strategist_view(quant_summary),
        )
        risk_view = _extract_view(
            risk_result,
            fallback=build_risk_view(quant_summary),
        )

        strategist_engine = strategist_result.get("engine")
        risk_engine = risk_result.get("engine")
        if strategist_engine == "opencode" and risk_engine == "opencode":
            effective_engine = "opencode"
            model_name = _resolve_model_name(strategist_result, risk_result)
        else:
            effective_engine = "fallback"
            model_name = "deterministic-fallback"
    else:
        strategist_view = build_strategist_view(quant_summary)
        risk_view = build_risk_view(quant_summary)
        effective_engine = "fallback"
        model_name = "deterministic-fallback"

    synthesis = synthesize_macro_analysis(quant_summary, strategist_view, risk_view)

    resolved_run_id = run_id or str(uuid4())

    persist_payload: dict[str, object] = {
        "run_id": resolved_run_id,
        "as_of": effective_as_of.isoformat(),
        "engine": effective_engine,
        "model": model_name,
        **synthesis,
    }

    repository.write_macro_analysis_result(persist_payload)

    return {
        "status": "success",
        "run_id": resolved_run_id,
        "as_of": effective_as_of.isoformat(),
        "regime": synthesis["regime"],
        "confidence": synthesis["confidence"],
        "engine": effective_engine,
        "model": model_name,
        "metric_keys": resolved_metric_keys,
        "metrics_with_data": sorted(series_by_metric.keys()),
    }

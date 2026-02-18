import os
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Optional, Protocol
from uuid import uuid4

from .agent_views import (
    LlmProviderProtocol,
    build_provider_from_env,
    build_risk_view,
    build_strategist_view,
    synthesize_macro_analysis,
)
from .macro_analysis import analyze_quant_regime, prepare_metric_series


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


def run_macro_analysis_flow(
    repository: MacroAnalysisRepositoryProtocol,
    metric_keys: Optional[Sequence[str]] = None,
    as_of: Optional[datetime] = None,
    limit: int = 120,
    provider: Optional[LlmProviderProtocol] = None,
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

    effective_provider = provider or build_provider_from_env()
    strategist_view = build_strategist_view(quant_summary, provider=effective_provider)
    risk_view = build_risk_view(quant_summary, provider=effective_provider)
    synthesis = synthesize_macro_analysis(quant_summary, strategist_view, risk_view)

    resolved_run_id = run_id or str(uuid4())
    model_name = (
        effective_provider.model_name
        if effective_provider is not None
        else "deterministic-fallback"
    )

    persist_payload: dict[str, object] = {
        "run_id": resolved_run_id,
        "as_of": effective_as_of.isoformat(),
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
        "model": model_name,
        "metric_keys": resolved_metric_keys,
        "metrics_with_data": sorted(series_by_metric.keys()),
    }

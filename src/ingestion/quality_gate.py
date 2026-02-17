from dataclasses import dataclass


@dataclass(frozen=True)
class BatchMetrics:
    freshness: bool
    completeness: bool
    schema_drift: bool
    license_ok: bool


@dataclass(frozen=True)
class QualityDecision:
    promote: bool
    route: str


def evaluate_quality(metrics: BatchMetrics) -> QualityDecision:
    passed = (
        metrics.freshness
        and metrics.completeness
        and not metrics.schema_drift
        and metrics.license_ok
    )
    if passed:
        return QualityDecision(promote=True, route="canonical")
    return QualityDecision(promote=False, route="quarantine")

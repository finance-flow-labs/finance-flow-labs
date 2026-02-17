import importlib


quality_gate = importlib.import_module("src.ingestion.quality_gate")
BatchMetrics = quality_gate.BatchMetrics
evaluate_quality = quality_gate.evaluate_quality


def test_quality_gate_routes_failed_batch_to_quarantine():
    metrics = BatchMetrics(
        freshness=False,
        completeness=True,
        schema_drift=False,
        license_ok=True,
    )
    result = evaluate_quality(metrics)
    assert result.promote is False
    assert result.route == "quarantine"


def test_quality_gate_promotes_passing_batch():
    metrics = BatchMetrics(
        freshness=True,
        completeness=True,
        schema_drift=False,
        license_ok=True,
    )
    result = evaluate_quality(metrics)
    assert result.promote is True
    assert result.route == "canonical"

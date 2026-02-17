import importlib


source_registry = importlib.import_module("src.ingestion.source_registry")
SourceDescriptor = source_registry.SourceDescriptor
evaluate_source = source_registry.evaluate_source


def test_source_gate_rejects_low_legal():
    src = SourceDescriptor(
        name="bronze_api",
        utility=5,
        reliability=4,
        legal=2,
        cost=3,
        maintenance=3,
    )
    result = evaluate_source(src)
    assert result.admitted is False


def test_source_gate_accepts_when_hard_gates_pass():
    src = SourceDescriptor(
        name="gold_api",
        utility=5,
        reliability=4,
        legal=4,
        cost=3,
        maintenance=3,
    )
    result = evaluate_source(src)
    assert result.admitted is True
    assert result.score > 0

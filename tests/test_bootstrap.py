import importlib


pipeline = importlib.import_module("src.ingestion.pipeline")


def test_pipeline_module_loads():
    assert hasattr(pipeline, "build_pipeline")


def test_pipeline_has_orchestration_entrypoint():
    assert hasattr(pipeline, "run_pipeline")

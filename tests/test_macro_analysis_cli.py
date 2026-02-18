import importlib
import types


cli = importlib.import_module("src.ingestion.cli")


def test_cli_exposes_run_macro_analysis_command():
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "run-macro-analysis",
            "--metric-key",
            "CPIAUCSL",
            "--metric-key",
            "KOR_BASE_RATE",
            "--as-of",
            "2026-02-18T00:00:00+00:00",
            "--limit",
            "50",
            "--analysis-engine",
            "fallback",
        ]
    )

    assert args.command == "run-macro-analysis"
    assert args.metric_key == ["CPIAUCSL", "KOR_BASE_RATE"]
    assert args.as_of == "2026-02-18T00:00:00+00:00"
    assert args.limit == 50
    assert args.analysis_engine == "fallback"


def test_run_macro_analysis_command_calls_flow_runner(monkeypatch):
    calls = {}

    class FakeRepository:
        def __init__(self, dsn):
            calls["dsn"] = dsn

    def fake_run_macro_analysis_flow(*, repository, metric_keys, as_of, limit, analysis_engine):
        calls["repository_type"] = type(repository).__name__
        calls["metric_keys"] = metric_keys
        calls["as_of"] = as_of
        calls["limit"] = limit
        calls["analysis_engine"] = analysis_engine
        return {"status": "success", "run_id": "run-1"}

    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://example")
    monkeypatch.setattr(cli, "PostgresRepository", FakeRepository)

    original_import_module = cli.importlib.import_module

    def patched_import_module(name):
        if name == "src.research.flow_runner":
            return types.SimpleNamespace(run_macro_analysis_flow=fake_run_macro_analysis_flow)
        return original_import_module(name)

    monkeypatch.setattr(cli.importlib, "import_module", patched_import_module)

    summary = cli.run_macro_analysis_command(
        metric_keys=["CPIAUCSL"],
        as_of="2026-02-18T00:00:00+00:00",
        limit=77,
        analysis_engine="fallback",
    )

    assert summary["status"] == "success"
    assert calls["dsn"] == "postgresql://example"
    assert calls["repository_type"] == "FakeRepository"
    assert calls["metric_keys"] == ["CPIAUCSL"]
    assert calls["limit"] == 77
    assert calls["analysis_engine"] == "fallback"


def test_cli_main_runs_macro_analysis_command(capsys, monkeypatch):
    monkeypatch.setattr(
        cli,
        "run_macro_analysis_command",
        lambda metric_keys, as_of, limit, analysis_engine: {
            "status": "success",
            "metric_keys": metric_keys,
            "as_of": as_of,
            "limit": limit,
            "engine": analysis_engine,
        },
    )

    exit_code = cli.main(
        [
            "run-macro-analysis",
            "--metric-key",
            "CPIAUCSL",
            "--limit",
            "21",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"status": "success"' in captured.out
    assert '"limit": 21' in captured.out
    assert '"engine": "opencode"' in captured.out

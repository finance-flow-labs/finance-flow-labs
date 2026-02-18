import importlib


cli = importlib.import_module("src.ingestion.cli")


def test_cli_exposes_manual_update_command():
    parser = cli.build_parser()
    args = parser.parse_args(["run-update", "--source", "sec_edgar"])

    assert args.command == "run-update"
    assert args.source == "sec_edgar"


def test_cli_exposes_macro_analysis_command():
    parser = cli.build_parser()
    args = parser.parse_args(["run-macro-analysis", "--metric-key", "CPIAUCSL"])

    assert args.command == "run-macro-analysis"
    assert args.metric_key == ["CPIAUCSL"]

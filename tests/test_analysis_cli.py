import argparse
import json

import src.analysis.cli as analysis_cli


def test_analysis_cli_exposes_stock_fmp_subcommand() -> None:
    parser = analysis_cli.build_parser()
    args = parser.parse_args(["stock", "fmp", "GOOGL"])

    assert args.command == "stock"
    assert args.market == "fmp"
    assert args.query == "GOOGL"
    assert args.limit == 5


def test_cmd_stock_fmp_uses_fmp_client(monkeypatch, capsys) -> None:
    class FakeFmpClient:
        def fetch_snapshot(self, query: str, limit: int):
            assert query == "GOOGL"
            assert limit == 7
            return {
                "query": query,
                "symbol": "GOOGL",
                "quote": {"price": 180.0},
                "errors": [],
            }

    monkeypatch.setattr(analysis_cli, "FmpStockClient", FakeFmpClient)

    args = argparse.Namespace(market="fmp", query="GOOGL", limit=7, year=None)
    analysis_cli.cmd_stock(args)

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["symbol"] == "GOOGL"
    assert payload["quote"]["price"] == 180.0

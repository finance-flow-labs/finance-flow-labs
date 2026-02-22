import importlib

import pytest


cli = importlib.import_module("src.ingestion.cli")


def test_cli_exposes_manual_update_command():
    parser = cli.build_parser()
    args = parser.parse_args(["run-update", "--source", "sec_edgar"])

    assert args.command == "run-update"
    assert args.source == "sec_edgar"


def test_cli_exposes_expected_vs_realized_command_with_defaults():
    parser = cli.build_parser()
    args = parser.parse_args(["expected-vs-realized"])

    assert args.command == "expected-vs-realized"
    assert args.horizon == "1M"
    assert args.limit == 50


def test_read_expected_vs_realized_command_requires_database_url(monkeypatch):
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValueError):
        cli.read_expected_vs_realized_command()


def test_read_expected_vs_realized_command_uses_postgres_repository(monkeypatch):
    class FakeRepository:
        def __init__(self, dsn: str) -> None:
            self.dsn = dsn

        def read_expected_vs_realized(self, horizon: str, limit: int):
            assert horizon == "3M"
            assert limit == 10
            return [{"horizon": horizon, "limit": limit, "dsn": self.dsn}]

    monkeypatch.setenv("DATABASE_URL", "postgres://example")
    monkeypatch.setattr(cli, "PostgresRepository", FakeRepository)

    rows = cli.read_expected_vs_realized_command(horizon="3M", limit=10)

    assert rows == [{"horizon": "3M", "limit": 10, "dsn": "postgres://example"}]

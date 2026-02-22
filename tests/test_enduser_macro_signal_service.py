from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.enduser.macro_signal_reader import read_latest_macro_regime_signal


class _Repo:
    def __init__(self, rows):
        self._rows = rows

    def read_latest_macro_analysis(self, limit=1):
        return self._rows


def test_read_latest_macro_regime_signal_happy_path():
    as_of = datetime.now(timezone.utc).isoformat()
    payload = read_latest_macro_regime_signal(
        "postgres://example",
        repository_factory=lambda _dsn: _Repo(
            [
                {
                    "run_id": "run-1",
                    "regime": "risk_on",
                    "confidence": 0.82,
                    "reason_codes": ["cpi_cooling"],
                    "as_of": as_of,
                    "evidence_hard": [{"source": "fred"}],
                    "evidence_soft": [{"source": "news"}],
                }
            ]
        ),
    )

    assert payload["status"] == "ok"
    assert payload["regime"] == "risk_on"
    assert payload["lineage_id"] == "run-1"
    assert payload["source_tags"] == ["macro_analysis_results"]
    assert payload["freshness_days"] == 7


def test_read_latest_macro_regime_signal_missing_row():
    payload = read_latest_macro_regime_signal(
        "postgres://example",
        repository_factory=lambda _dsn: _Repo([]),
    )

    assert payload["status"] == "missing"
    assert payload["reason"] == "missing"


def test_read_latest_macro_regime_signal_stale_row():
    stale_as_of = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    payload = read_latest_macro_regime_signal(
        "postgres://example",
        repository_factory=lambda _dsn: _Repo(
            [{"run_id": "run-2", "regime": "neutral", "confidence": 0.5, "as_of": stale_as_of}]
        ),
    )

    assert payload["status"] == "stale"
    assert payload["reason"] == "stale"


def test_read_latest_macro_regime_signal_malformed_row():
    payload = read_latest_macro_regime_signal(
        "postgres://example",
        repository_factory=lambda _dsn: _Repo([{"run_id": "run-3", "confidence": 0.4}]),
    )

    assert payload["status"] == "error"
    assert payload["reason"] == "malformed"

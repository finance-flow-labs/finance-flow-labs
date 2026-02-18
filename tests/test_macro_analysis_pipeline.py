from datetime import datetime, timezone
import importlib


flow_runner = importlib.import_module("src.research.flow_runner")


class FakeRepository:
    def __init__(self, rows_by_metric):
        self.rows_by_metric = rows_by_metric
        self.saved_results = []

    def read_macro_series_points(self, metric_key, limit=100):
        rows = self.rows_by_metric.get(metric_key, [])
        return list(rows)[:limit]

    def write_macro_analysis_result(self, result):
        self.saved_results.append(dict(result))


def test_macro_analysis_flow_fallback_persists_complete_payload():
    repo = FakeRepository(
        {
            "CPIAUCSL": [
                {
                    "as_of": datetime(2026, 1, 1, tzinfo=timezone.utc),
                    "value": 3.2,
                },
                {
                    "as_of": datetime(2026, 2, 1, tzinfo=timezone.utc),
                    "value": 3.0,
                },
            ],
            "KOR_BASE_RATE": [
                {
                    "as_of": datetime(2026, 1, 1, tzinfo=timezone.utc),
                    "value": 3.5,
                },
                {
                    "as_of": datetime(2026, 2, 1, tzinfo=timezone.utc),
                    "value": 3.25,
                },
            ],
        }
    )

    summary = flow_runner.run_macro_analysis_flow(
        repository=repo,
        metric_keys=["CPIAUCSL", "KOR_BASE_RATE"],
        as_of=datetime(2026, 2, 18, tzinfo=timezone.utc),
        limit=120,
        analysis_engine="fallback",
        run_id="run-fixed",
    )

    assert summary["status"] == "success"
    assert summary["run_id"] == "run-fixed"
    assert summary["engine"] == "fallback"
    assert summary["model"] == "deterministic-fallback"
    assert len(repo.saved_results) == 1

    payload = repo.saved_results[0]
    required_keys = {
        "run_id",
        "as_of",
        "regime",
        "confidence",
        "base_case",
        "bull_case",
        "bear_case",
        "reason_codes",
        "risk_flags",
        "triggers",
        "narrative",
        "engine",
        "model",
    }
    assert required_keys.issubset(payload.keys())
    assert payload["run_id"] == "run-fixed"
    assert payload["engine"] == "fallback"
    assert payload["model"] == "deterministic-fallback"
    assert isinstance(payload["reason_codes"], list)
    assert isinstance(payload["risk_flags"], list)
    assert isinstance(payload["triggers"], list)


def test_macro_analysis_flow_is_deterministic_for_same_input():
    rows = {
        "CPIAUCSL": [
            {
                "as_of": datetime(2026, 1, 1, tzinfo=timezone.utc),
                "value": 3.2,
            },
            {
                "as_of": datetime(2026, 2, 1, tzinfo=timezone.utc),
                "value": 3.0,
            },
        ]
    }
    as_of = datetime(2026, 2, 18, tzinfo=timezone.utc)

    repo_a = FakeRepository(rows)
    repo_b = FakeRepository(rows)

    flow_runner.run_macro_analysis_flow(
        repository=repo_a,
        metric_keys=["CPIAUCSL"],
        as_of=as_of,
        limit=120,
        analysis_engine="fallback",
        run_id="run-det",
    )
    flow_runner.run_macro_analysis_flow(
        repository=repo_b,
        metric_keys=["CPIAUCSL"],
        as_of=as_of,
        limit=120,
        analysis_engine="fallback",
        run_id="run-det",
    )

    payload_a = repo_a.saved_results[0]
    payload_b = repo_b.saved_results[0]

    stable_keys = [
        "run_id",
        "as_of",
        "regime",
        "confidence",
        "base_case",
        "bull_case",
        "bear_case",
        "reason_codes",
        "risk_flags",
        "triggers",
        "narrative",
        "engine",
        "model",
    ]

    for key in stable_keys:
        assert payload_a[key] == payload_b[key]


def test_macro_analysis_flow_opencode_uses_agent_runner(monkeypatch):
    repo = FakeRepository(
        {
            "CPIAUCSL": [
                {
                    "as_of": datetime(2026, 1, 1, tzinfo=timezone.utc),
                    "value": 3.2,
                },
                {
                    "as_of": datetime(2026, 2, 1, tzinfo=timezone.utc),
                    "value": 3.0,
                },
            ]
        }
    )

    monkeypatch.setattr(
        flow_runner.opencode_runner,
        "generate_strategist_view",
        lambda quant_summary: {
            "engine": "opencode",
            "model": "gpt-5.3-codex",
            "view": {
                "agent": "strategist",
                "summary": "Strategist summary",
                "base_case": "Base case",
                "bull_case": "Bull case",
                "bear_case": "Bear case",
                "reason_codes": ["CPIAUCSL:down"],
                "triggers": ["next_release:CPIAUCSL"],
            },
        },
    )
    monkeypatch.setattr(
        flow_runner.opencode_runner,
        "generate_risk_view",
        lambda quant_summary: {
            "engine": "opencode",
            "model": "gpt-5.3-codex",
            "view": {
                "agent": "risk",
                "summary": "Risk summary",
                "risk_flags": ["event_risk"],
                "triggers": ["next_release:CPIAUCSL"],
            },
        },
    )

    summary = flow_runner.run_macro_analysis_flow(
        repository=repo,
        metric_keys=["CPIAUCSL"],
        as_of=datetime(2026, 2, 18, tzinfo=timezone.utc),
        limit=120,
        analysis_engine="opencode",
        run_id="run-opencode",
    )

    assert summary["engine"] == "opencode"
    assert summary["model"] == "gpt-5.3-codex"
    assert repo.saved_results[0]["narrative"] == "Strategist summary Risk summary"

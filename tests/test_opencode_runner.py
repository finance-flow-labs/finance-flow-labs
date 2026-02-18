import importlib
import json
import subprocess


opencode_runner = importlib.import_module("src.research.opencode_runner")


def test_generate_strategist_view_parses_strict_json(monkeypatch):
    stdout = json.dumps(
        {
            "summary": "Macro momentum is improving.",
            "base_case": "Growth broadens while inflation cools.",
            "bull_case": "Policy easing supports risk assets.",
            "bear_case": "Inflation re-accelerates and tightening resumes.",
            "reason_codes": ["CPIAUCSL:down"],
            "triggers": ["next_release:CPIAUCSL"],
            "model": "gpt-5.3-codex",
        }
    )

    def fake_run(command, capture_output, text, timeout, check):
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=stdout,
            stderr="",
        )

    monkeypatch.setattr(opencode_runner.subprocess, "run", fake_run)

    result = opencode_runner.generate_strategist_view(
        {
            "regime": "expansion",
            "reason_codes": ["CPIAUCSL:down"],
            "triggers": ["next_release:CPIAUCSL"],
        }
    )

    assert result["engine"] == "opencode"
    assert result["model"] == "gpt-5.3-codex"
    assert result["view"]["summary"] == "Macro momentum is improving."


def test_generate_strategist_view_falls_back_on_parse_failure(monkeypatch):
    def fake_run(command, capture_output, text, timeout, check):
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="not-json",
            stderr="",
        )

    monkeypatch.setattr(opencode_runner.subprocess, "run", fake_run)

    result = opencode_runner.generate_strategist_view(
        {
            "regime": "neutral",
            "reason_codes": ["insufficient_signals"],
            "triggers": ["next_release:CPIAUCSL"],
        }
    )

    assert result["engine"] == "fallback"
    assert result["model"] == "deterministic-fallback"
    assert result["view"]["agent"] == "strategist"
    assert "Strategist view:" in result["view"]["summary"]


def test_generate_risk_view_falls_back_on_timeout(monkeypatch):
    def fake_run(command, capture_output, text, timeout, check):
        raise subprocess.TimeoutExpired(cmd=command, timeout=timeout)

    monkeypatch.setattr(opencode_runner.subprocess, "run", fake_run)

    result = opencode_runner.generate_risk_view(
        {
            "regime": "slowdown",
            "risk_flags": ["credit_stress"],
            "triggers": ["next_release:CPIAUCSL"],
        },
        timeout_seconds=7,
    )

    assert result["engine"] == "fallback"
    assert result["model"] == "deterministic-fallback"
    assert result["view"]["agent"] == "risk"
    assert "Risk view:" in result["view"]["summary"]

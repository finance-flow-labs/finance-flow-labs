from __future__ import annotations

import importlib
import types

import pytest


class _TabContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_run_enduser_app_renders_portfolio_and_signals_tabs(monkeypatch):
    calls: dict[str, object] = {"tabs": None, "info": [], "subheader": []}

    def set_page_config(**kwargs):
        calls["page_config"] = kwargs

    def title(text: str):
        calls["title"] = text

    def tabs(labels: list[str]):
        calls["tabs"] = labels
        return [_TabContext(), _TabContext()]

    def subheader(text: str):
        calls["subheader"].append(text)

    def info(text: str):
        calls["info"].append(text)

    def markdown(text: str):
        calls.setdefault("markdown", []).append(text)

    def caption(text: str):
        calls.setdefault("captions", []).append(text)

    def write(text: str):
        calls.setdefault("write", []).append(text)

    def progress(value: float):
        calls.setdefault("progress", []).append(value)

    fake_streamlit = types.SimpleNamespace(
        set_page_config=set_page_config,
        title=title,
        caption=caption,
        tabs=tabs,
        info=info,
        subheader=subheader,
        markdown=markdown,
        write=write,
        progress=progress,
        warning=lambda text: calls.setdefault("warning", []).append(text),
    )

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_streamlit)
    app = importlib.import_module("src.enduser.app")
    monkeypatch.setattr(app, "_render_portfolio_tab", lambda _st, dsn: calls.setdefault("portfolio_dsn", dsn))
    monkeypatch.setattr(
        app,
        "read_latest_macro_regime_signal",
        lambda _dsn: {
            "status": "ok",
            "regime": "risk_on",
            "confidence": 0.7,
            "drivers": ["cpi_cooling"],
            "as_of": "2026-02-22T19:00:00Z",
            "lineage_id": "run-1",
        },
    )

    app.run_enduser_app("postgres://example")

    assert calls["tabs"] == ["Portfolio", "Signals"]
    assert calls["portfolio_dsn"] == "postgres://example"
    assert calls["subheader"] == ["Macro regime signal"]
    assert calls["info"] == ["More signal cards coming soon"]


def test_run_enduser_app_wires_reader_payload_into_signal_card(monkeypatch):
    calls: dict[str, object] = {"reader_dsn": None, "render_payload": None, "render_dsn": None}

    class _TabContext:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    fake_streamlit = types.SimpleNamespace(
        set_page_config=lambda **_: None,
        title=lambda *_: None,
        caption=lambda *_: None,
        tabs=lambda _labels: [_TabContext(), _TabContext()],
        info=lambda *_: None,
    )

    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_streamlit)
    app = importlib.import_module("src.enduser.app")

    expected_payload = {
        "status": "ok",
        "regime": "risk_off",
        "confidence": 0.61,
        "as_of": "2026-02-22T21:30:00Z",
    }

    def _fake_reader(dsn: str):
        calls["reader_dsn"] = dsn
        return expected_payload

    def _fake_render(*, regime_signal, dsn=None):
        calls["render_payload"] = regime_signal
        calls["render_dsn"] = dsn

    monkeypatch.setattr(app, "_render_portfolio_tab", lambda _st, _dsn: None)
    monkeypatch.setattr(app, "read_latest_macro_regime_signal", _fake_reader)
    monkeypatch.setattr(app, "render_macro_regime_card", _fake_render)

    app.run_enduser_app("postgres://macro-signal")

    assert calls["reader_dsn"] == "postgres://macro-signal"
    assert calls["render_payload"] == expected_payload
    assert calls["render_dsn"] == "postgres://macro-signal"


def test_render_portfolio_tab_shows_empty_info_when_no_snapshot(monkeypatch):
    calls: dict[str, object] = {"info": [], "line_chart": []}

    class _Column:
        def metric(self, label: str, value: str):
            calls.setdefault("metrics", []).append((label, value))

    fake_streamlit = types.SimpleNamespace(
        info=lambda text: calls["info"].append(text),
        warning=lambda text: calls.setdefault("warning", []).append(text),
        columns=lambda count: [_Column() for _ in range(count)],
        line_chart=lambda *args, **kwargs: calls["line_chart"].append((args, kwargs)),
    )

    app = importlib.import_module("src.enduser.app")
    monkeypatch.setattr(app, "PostgresRepository", lambda dsn: object())
    monkeypatch.setattr(app, "build_performance_view", lambda _repo: {"nav_series": []})

    app._render_portfolio_tab(fake_streamlit, "postgres://example")

    assert calls["info"] == ["포트폴리오 스냅샷이 없습니다."]
    assert calls["line_chart"] == []


def test_render_portfolio_tab_renders_metrics_chart_allocation_and_leverage(monkeypatch):
    calls: dict[str, object] = {"metrics": [], "line_chart": [], "bar_chart": []}

    class _Column:
        def metric(self, label: str, value: str):
            calls["metrics"].append((label, value))

    fake_streamlit = types.SimpleNamespace(
        info=lambda text: calls.setdefault("info", []).append(text),
        warning=lambda text: calls.setdefault("warning", []).append(text),
        caption=lambda text: calls.setdefault("caption", []).append(text),
        subheader=lambda text: calls.setdefault("subheader", []).append(text),
        columns=lambda count: [_Column() for _ in range(count)],
        line_chart=lambda *args, **kwargs: calls["line_chart"].append((args, kwargs)),
        bar_chart=lambda *args, **kwargs: calls["bar_chart"].append((args, kwargs)),
    )

    performance_payload = {
        "total_return_pct": 12.34,
        "mdd_pct": -21.0,
        "sharpe_ratio": 1.23,
        "alpha_pct": 2.5,
        "mdd_alert": True,
        "policy_mdd_limit_pct": -30.0,
        "mdd_policy_buffer_pp": 9.0,
        "us_weight_pct": 45.0,
        "kr_weight_pct": 25.0,
        "crypto_weight_pct": 20.0,
        "other_weight_pct": 10.0,
        "leverage_weight_pct": 25.0,
        "leverage_cap_pct": 20.0,
        "leverage_cap_breached": True,
        "nav_series": [
            {"as_of": "2026-01-01", "nav": 1000},
            {"as_of": "2026-01-02", "nav": 1100},
        ],
        "benchmark_series": [
            {"as_of": "2026-01-02", "benchmark_nav": 1.02},
        ],
    }

    app = importlib.import_module("src.enduser.app")
    monkeypatch.setattr(app, "PostgresRepository", lambda dsn: object())
    monkeypatch.setattr(app, "build_performance_view", lambda _repo: performance_payload)

    app._render_portfolio_tab(fake_streamlit, "postgres://example")

    labels = [label for label, _ in calls["metrics"]]
    assert labels == ["총수익률", "MDD", "Sharpe", "알파(vs 벤치마크)"]
    assert calls["line_chart"], "expected line_chart call"
    assert calls["bar_chart"], "expected allocation chart"
    assert "자산 배분" in calls.get("subheader", [])
    warnings = calls.get("warning", [])
    assert any("MDD" in text for text in warnings)
    assert any("레버리지 슬리브" in text for text in warnings)


def test_enduser_entrypoint_requires_database_url(monkeypatch):
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    enduser_app = importlib.import_module("enduser_app")
    with pytest.raises(ValueError, match="DATABASE_URL"):
        enduser_app.main()

from __future__ import annotations

import importlib
import sys
import types


def test_render_macro_regime_card_with_signal(monkeypatch):
    calls: dict[str, list] = {
        "subheader": [],
        "markdown": [],
        "caption": [],
        "write": [],
        "progress": [],
        "info": [],
    }

    fake_streamlit = types.SimpleNamespace(
        subheader=lambda text: calls["subheader"].append(text),
        markdown=lambda text: calls["markdown"].append(text),
        caption=lambda text: calls["caption"].append(text),
        write=lambda text: calls["write"].append(text),
        progress=lambda value: calls["progress"].append(value),
        info=lambda text: calls["info"].append(text),
        warning=lambda text: calls.setdefault("warning", []).append(text),
    )

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    sys.modules.pop("src.enduser.signals", None)
    signals = importlib.import_module("src.enduser.signals")

    signals.render_macro_regime_card(
        {
            "regime": "risk_on",
            "confidence": 0.8,
            "drivers": ["금리 하락 방향", "실업률 안정", "CPI 둔화", "ignored"],
            "as_of": "2026-02-22T18:30:00Z",
            "source_tags": ["macro_analysis_results"],
            "freshness_days": 7,
            "evidence_hard": ["FRED:CPIAUCSL 3m down", "FRED:UNRATE stable"],
            "evidence_soft": ["Fed commentary softer"],
        }
    )

    assert calls["subheader"] == ["Macro regime signal"]
    assert calls["markdown"] == ["### 🟢 Risk-On"]
    assert calls["caption"] == [
        "as_of: 2026-02-22T18:30:00Z",
        "source_tags: macro_analysis_results",
        "freshness_policy: stale after 7d",
    ]
    assert calls["progress"] == [0.8]
    assert "핵심 드라이버 (Top 3):" in calls["write"]
    assert calls["write"].count("• 금리 하락 방향") == 1
    assert calls["write"].count("• 실업률 안정") == 1
    assert calls["write"].count("• CPI 둔화") == 1
    assert "HARD evidence:" in calls["write"]
    assert "SOFT evidence:" in calls["write"]
    assert calls["write"].count("• FRED:CPIAUCSL 3m down") == 1
    assert calls["write"].count("• Fed commentary softer") == 1


def test_render_macro_regime_card_placeholder_when_data_missing(monkeypatch):
    calls: dict[str, list] = {"subheader": [], "info": [], "warning": [], "caption": []}

    fake_streamlit = types.SimpleNamespace(
        subheader=lambda text: calls["subheader"].append(text),
        info=lambda text: calls["info"].append(text),
        warning=lambda text: calls["warning"].append(text),
        caption=lambda text: calls["caption"].append(text),
    )

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    sys.modules.pop("src.enduser.signals", None)
    signals = importlib.import_module("src.enduser.signals")

    signals.render_macro_regime_card(None)

    assert calls["subheader"] == ["Macro regime signal"]
    assert calls["info"] == ["No macro regime signal yet. Analysis pipeline data is pending."]
    assert calls["warning"] == []
    assert calls["caption"] == ["next_action: run macro-analysis ingestion and refresh Signals tab"]


def test_render_macro_regime_card_shows_freshness_policy_when_zero_days(monkeypatch):
    calls: dict[str, list] = {"caption": []}

    fake_streamlit = types.SimpleNamespace(
        subheader=lambda *_: None,
        markdown=lambda *_: None,
        caption=lambda text: calls["caption"].append(text),
        write=lambda *_: None,
        progress=lambda *_: None,
        info=lambda *_: None,
        warning=lambda *_: None,
    )

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    sys.modules.pop("src.enduser.signals", None)
    signals = importlib.import_module("src.enduser.signals")

    signals.render_macro_regime_card(
        {
            "regime": "neutral",
            "confidence": 0.5,
            "as_of": "2026-02-22T00:00:00Z",
            "freshness_days": 0,
        }
    )

    assert "freshness_policy: stale after 0d" in calls["caption"]


def test_render_macro_regime_card_shows_stale_state(monkeypatch):
    calls: dict[str, list] = {"subheader": [], "warning": [], "caption": []}

    fake_streamlit = types.SimpleNamespace(
        subheader=lambda text: calls["subheader"].append(text),
        warning=lambda text: calls["warning"].append(text),
        markdown=lambda *_: None,
        caption=lambda text: calls["caption"].append(text),
        write=lambda *_: None,
        progress=lambda *_: None,
    )

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    sys.modules.pop("src.enduser.signals", None)
    signals = importlib.import_module("src.enduser.signals")

    signals.render_macro_regime_card(
        {"status": "stale", "message": "Latest macro regime signal is stale (> 7 days).", "regime": "neutral", "confidence": 0.4, "as_of": "2026-02-01T00:00:00Z"}
    )

    assert calls["subheader"] == ["Macro regime signal"]
    assert calls["warning"] == ["[stale] Latest macro regime signal is stale (> 7 days)."]
    assert calls["caption"] == ["next_action: rerun macro-analysis pipeline to refresh as_of", "as_of: 2026-02-01T00:00:00Z"]

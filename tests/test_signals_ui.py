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
        }
    )

    assert calls["subheader"] == ["Macro regime signal"]
    assert calls["markdown"] == ["### 🟢 Risk-On"]
    assert calls["caption"] == ["as_of: 2026-02-22T18:30:00Z"]
    assert calls["progress"] == [0.8]
    assert "핵심 드라이버 (Top 3):" in calls["write"]
    assert calls["write"].count("• 금리 하락 방향") == 1
    assert calls["write"].count("• 실업률 안정") == 1
    assert calls["write"].count("• CPI 둔화") == 1


def test_render_macro_regime_card_placeholder_when_data_missing(monkeypatch):
    calls: dict[str, list] = {"subheader": [], "info": []}

    fake_streamlit = types.SimpleNamespace(
        subheader=lambda text: calls["subheader"].append(text),
        info=lambda text: calls["info"].append(text),
    )

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    sys.modules.pop("src.enduser.signals", None)
    signals = importlib.import_module("src.enduser.signals")

    signals.render_macro_regime_card(None)

    assert calls["subheader"] == ["Macro regime signal"]
    assert calls["info"] == ["No macro regime signal yet. Analysis pipeline data is pending."]

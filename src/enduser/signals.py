from __future__ import annotations

from datetime import date, datetime
from typing import Any

import streamlit as st

_REGIME_META: dict[str, tuple[str, str]] = {
    "risk_on": ("🟢", "Risk-On"),
    "risk_off": ("🔴", "Risk-Off"),
    "neutral": ("⚪", "Neutral"),
}


def _normalize_as_of(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and value.strip():
        return value
    return "N/A"


def render_macro_regime_card(regime_signal: dict[str, Any] | None) -> None:
    st.subheader("Macro regime signal")

    if not regime_signal:
        st.info("No macro regime signal yet. Analysis pipeline data is pending.")
        return

    regime_key = str(regime_signal.get("regime", "neutral")).strip().lower().replace("-", "_")
    emoji, regime_label = _REGIME_META.get(regime_key, _REGIME_META["neutral"])

    confidence_raw = regime_signal.get("confidence", 0.0)
    try:
        confidence = max(0.0, min(float(confidence_raw), 1.0))
    except (TypeError, ValueError):
        confidence = 0.0

    drivers = [str(item) for item in regime_signal.get("drivers", []) if str(item).strip()][:3]

    st.markdown(f"### {emoji} {regime_label}")
    st.caption(f"as_of: {_normalize_as_of(regime_signal.get('as_of'))}")

    st.write(f"신뢰도: {confidence * 100:.0f}%")
    st.progress(confidence)

    st.write("핵심 드라이버 (Top 3):")
    if drivers:
        for driver in drivers:
            st.write(f"• {driver}")
    else:
        st.write("• Driver data unavailable")

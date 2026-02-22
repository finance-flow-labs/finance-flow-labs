from __future__ import annotations

import streamlit as st

from src.enduser.signals import render_macro_regime_card


def run_enduser_app(dsn: str) -> None:
    st.set_page_config(page_title="finance-flow-labs · End-user", layout="wide")
    st.title("finance-flow-labs · End-user")
    st.caption("Investor workspace (paper-trade intelligence).")

    portfolio_tab, signals_tab = st.tabs(["Portfolio", "Signals"])

    with portfolio_tab:
        st.info("Coming soon")

    with signals_tab:
        render_macro_regime_card(regime_signal=None)
        st.info("More signal cards coming soon")

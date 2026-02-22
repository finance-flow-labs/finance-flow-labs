from __future__ import annotations

import streamlit as st


def run_enduser_app(dsn: str) -> None:
    st.set_page_config(page_title="finance-flow-labs · End-user", layout="wide")
    st.title("finance-flow-labs · End-user")
    st.caption("Investor workspace (paper-trade intelligence).")

    portfolio_tab, signals_tab = st.tabs(["Portfolio", "Signals"])

    with portfolio_tab:
        st.info("Coming soon")

    with signals_tab:
        st.info("Coming soon")

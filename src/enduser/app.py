from __future__ import annotations

import importlib

from src.enduser.macro_signal_reader import read_latest_macro_regime_signal
from src.enduser.performance_service import build_performance_view
from src.enduser.signals import render_macro_regime_card
from src.ingestion.postgres_repository import PostgresRepository


def _format_pct(value: object, precision: int = 2) -> str:
    try:
        if value is None:
            return "n/a"
        return f"{float(value):.{precision}f}%"
    except (TypeError, ValueError):
        return "n/a"


def _format_ratio(value: object, precision: int = 2) -> str:
    try:
        if value is None:
            return "n/a"
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        return "n/a"


def _format_pp(value: object, precision: int = 2) -> str:
    try:
        if value is None:
            return "n/a"
        return f"{float(value):.{precision}f}%p"
    except (TypeError, ValueError):
        return "n/a"


def _render_portfolio_tab(st: object, dsn: str) -> None:
    repository = PostgresRepository(dsn=dsn)
    performance = build_performance_view(repository)

    nav_series = performance.get("nav_series", [])
    if not isinstance(nav_series, list) or not nav_series:
        st.info("포트폴리오 스냅샷이 없습니다.")
        return

    total_return_pct = performance.get("total_return_pct")
    mdd_pct = performance.get("mdd_pct")
    sharpe_ratio = performance.get("sharpe_ratio")
    alpha_pct = performance.get("alpha_pct")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총수익률", _format_pct(total_return_pct))
    c2.metric("MDD", _format_pct(mdd_pct))
    c3.metric("Sharpe", _format_ratio(sharpe_ratio))
    c4.metric("알파(vs 벤치마크)", _format_pct(alpha_pct))

    if bool(performance.get("mdd_alert")):
        policy_limit_pct = performance.get("policy_mdd_limit_pct")
        mdd_policy_buffer_pp = performance.get("mdd_policy_buffer_pp")
        if mdd_policy_buffer_pp is not None and float(mdd_policy_buffer_pp) > 0:
            st.warning(
                f"⚠️ MDD {_format_pct(mdd_pct)} — 정책 한계({_format_pct(policy_limit_pct)})까지 "
                f"{_format_pp(mdd_policy_buffer_pp)} 남음"
            )
        else:
            st.warning(
                f"⚠️ MDD {_format_pct(mdd_pct)} — 정책 한계({_format_pct(policy_limit_pct)})를 초과했습니다"
            )

    benchmark_series = performance.get("benchmark_series", [])
    benchmark_map: dict[str, float] = {}
    if isinstance(benchmark_series, list):
        for row in benchmark_series:
            if not isinstance(row, dict):
                continue
            as_of = row.get("as_of")
            benchmark_nav = row.get("benchmark_nav")
            if as_of is None or benchmark_nav is None:
                continue
            try:
                benchmark_map[str(as_of)] = float(benchmark_nav) * 100
            except (TypeError, ValueError):
                continue

    chart_rows: list[dict[str, object]] = []
    base_nav = float(nav_series[0].get("nav", 0) or 0)
    if base_nav > 0:
        for row in nav_series:
            if not isinstance(row, dict):
                continue
            as_of = str(row.get("as_of") or "")
            nav = row.get("nav")
            if not as_of:
                continue
            try:
                nav_value = float(nav)
            except (TypeError, ValueError):
                continue
            chart_rows.append(
                {
                    "as_of": as_of,
                    "portfolio_nav_index": (nav_value / base_nav) * 100,
                    "benchmark_nav_index": benchmark_map.get(as_of),
                }
            )

    if chart_rows:
        st.line_chart(
            chart_rows,
            x="as_of",
            y=["portfolio_nav_index", "benchmark_nav_index"],
        )

    allocation_pairs = [
        ("US", performance.get("us_weight_pct")),
        ("KR", performance.get("kr_weight_pct")),
        ("Crypto", performance.get("crypto_weight_pct")),
        ("기타", performance.get("other_weight_pct")),
    ]
    allocation_chart = {
        label: [float(weight)]
        for label, weight in allocation_pairs
        if weight is not None
    }
    if allocation_chart:
        st.subheader("자산 배분")
        st.bar_chart(allocation_chart)
        st.caption("정책 목표 가이드: US ~45% · KR ~25% · Crypto ~20%")

    leverage_weight_pct = performance.get("leverage_weight_pct")
    leverage_cap_pct = performance.get("leverage_cap_pct")
    if leverage_weight_pct is not None and leverage_cap_pct is not None:
        leverage_message = (
            f"레버리지 슬리브: {_format_pct(leverage_weight_pct)} / {_format_pct(leverage_cap_pct)} 상한"
        )
        if bool(performance.get("leverage_cap_breached")):
            st.warning(f"⚠️ {leverage_message}")
        else:
            st.caption(leverage_message)


def run_enduser_app(dsn: str, *, configure_page: bool = True) -> None:
    st = importlib.import_module("streamlit")

    if configure_page:
        st.set_page_config(page_title="finance-flow-labs · End-user", layout="wide")
    st.title("finance-flow-labs · End-user")
    st.caption("Investor workspace (paper-trade intelligence).")

    portfolio_tab, signals_tab = st.tabs(["Portfolio", "Signals"])

    with portfolio_tab:
        _render_portfolio_tab(st, dsn)

    with signals_tab:
        regime_signal = read_latest_macro_regime_signal(dsn)
        render_macro_regime_card(regime_signal=regime_signal, dsn=dsn)
        st.info("More signal cards coming soon")

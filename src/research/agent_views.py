from collections.abc import Mapping


def _coerce_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str)]


def _coerce_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return float(stripped)
        except ValueError:
            return default
    return default


def _fallback_base_case(regime: str) -> str:
    if regime == "expansion":
        return "Disinflation and easing pressure suggest improving macro momentum."
    if regime == "slowdown":
        return "Tight financial conditions and weaker momentum suggest a slowdown regime."
    return "Mixed signals indicate a neutral regime with limited directional conviction."


def _fallback_bull_case(regime: str) -> str:
    if regime == "expansion":
        return "Soft-landing conditions broaden and cyclical risk appetite improves."
    if regime == "slowdown":
        return "Inflation cools faster than expected and policy can pivot supportively."
    return "Macro data surprise to the upside while inflation remains contained."


def _fallback_bear_case(regime: str) -> str:
    if regime == "expansion":
        return "Inflation re-accelerates and policy tightening pressure returns."
    if regime == "slowdown":
        return "Growth deterioration accelerates and credit stress widens."
    return "Policy error or growth shock forces a downside repricing of risk assets."


def build_strategist_view(
    quant_summary: Mapping[str, object],
) -> dict[str, object]:
    regime = str(quant_summary.get("regime", "neutral"))
    reason_codes = _coerce_str_list(quant_summary.get("reason_codes", []))

    fallback_summary = (
        f"Strategist view: regime={regime}; key signals={', '.join(reason_codes[:3]) or 'insufficient_signals'}."
    )

    return {
        "agent": "strategist",
        "summary": fallback_summary,
        "base_case": _fallback_base_case(regime),
        "bull_case": _fallback_bull_case(regime),
        "bear_case": _fallback_bear_case(regime),
        "reason_codes": reason_codes,
        "triggers": _coerce_str_list(quant_summary.get("triggers", [])),
    }


def build_risk_view(
    quant_summary: Mapping[str, object],
) -> dict[str, object]:
    risk_flags = _coerce_str_list(quant_summary.get("risk_flags", []))
    fallback_summary = (
        "Risk view: "
        + (
            ", ".join(risk_flags)
            if risk_flags
            else "No acute risk flags from the current quant snapshot."
        )
    )

    triggers = _coerce_str_list(quant_summary.get("triggers", []))
    if not triggers:
        triggers = ["next_macro_release"]

    return {
        "agent": "risk",
        "summary": fallback_summary,
        "risk_flags": risk_flags,
        "triggers": triggers,
    }


def synthesize_macro_analysis(
    quant_summary: Mapping[str, object],
    strategist_view: Mapping[str, object],
    risk_view: Mapping[str, object],
) -> dict[str, object]:
    regime = str(quant_summary.get("regime", "neutral"))

    narrative_parts = [
        str(strategist_view.get("summary", "")).strip(),
        str(risk_view.get("summary", "")).strip(),
    ]
    narrative = " ".join(part for part in narrative_parts if part)

    reason_codes = sorted(
        {
            str(item)
            for item in [
                *[str(v) for v in _coerce_str_list(quant_summary.get("reason_codes", []))],
                *[str(v) for v in _coerce_str_list(strategist_view.get("reason_codes", []))],
            ]
            if item
        }
    )
    risk_flags = sorted(
        {
            str(item)
            for item in [
                *[str(v) for v in _coerce_str_list(quant_summary.get("risk_flags", []))],
                *[str(v) for v in _coerce_str_list(risk_view.get("risk_flags", []))],
            ]
            if item
        }
    )
    triggers = sorted(
        {
            str(item)
            for item in [
                *[str(v) for v in _coerce_str_list(quant_summary.get("triggers", []))],
                *[str(v) for v in _coerce_str_list(strategist_view.get("triggers", []))],
                *[str(v) for v in _coerce_str_list(risk_view.get("triggers", []))],
            ]
            if item
        }
    )

    return {
        "regime": regime,
        "confidence": _coerce_float(quant_summary.get("confidence", 0.0), default=0.0),
        "base_case": str(strategist_view.get("base_case", _fallback_base_case(regime))),
        "bull_case": str(strategist_view.get("bull_case", _fallback_bull_case(regime))),
        "bear_case": str(strategist_view.get("bear_case", _fallback_bear_case(regime))),
        "reason_codes": reason_codes,
        "risk_flags": risk_flags,
        "triggers": triggers,
        "narrative": narrative,
    }

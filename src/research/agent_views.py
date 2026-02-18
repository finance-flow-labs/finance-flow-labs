import json
import os
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from typing import Optional, Protocol


class LlmProviderProtocol(Protocol):
    model_name: str

    def complete(self, *, system_prompt: str, user_prompt: str) -> str: ...


class OpenAiChatProvider:
    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-5.3-codex",
        timeout_seconds: int = 20,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        request = urllib.request.Request(
            url="https://api.openai.com/v1/chat/completions",
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload).encode("utf-8"),
        )

        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            body = response.read().decode("utf-8")

        data = json.loads(body)
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""

        first = choices[0]
        if not isinstance(first, Mapping):
            return ""

        message = first.get("message")
        if not isinstance(message, Mapping):
            return ""

        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        return ""


def build_provider_from_env() -> Optional[LlmProviderProtocol]:
    provider = os.getenv("MACRO_LLM_PROVIDER", "openai").strip().lower()
    if provider not in {"", "openai"}:
        return None

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    model_name = os.getenv("OPENAI_MODEL", "gpt-5.3-codex").strip() or "gpt-5.3-codex"
    timeout_raw = os.getenv("OPENAI_TIMEOUT_SECONDS", "20").strip()
    timeout_seconds = int(timeout_raw) if timeout_raw.isdigit() else 20
    return OpenAiChatProvider(api_key=api_key, model_name=model_name, timeout_seconds=timeout_seconds)


def _render_with_provider(
    provider: Optional[LlmProviderProtocol],
    *,
    system_prompt: str,
    user_prompt: str,
    fallback: str,
) -> str:
    if provider is None:
        return fallback

    try:
        content = provider.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        if content:
            return content
        return fallback
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return fallback


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
    provider: Optional[LlmProviderProtocol] = None,
) -> dict[str, object]:
    regime = str(quant_summary.get("regime", "neutral"))
    reason_codes = [str(item) for item in quant_summary.get("reason_codes", []) if isinstance(item, str)]

    fallback_summary = (
        f"Strategist view: regime={regime}; key signals={', '.join(reason_codes[:3]) or 'insufficient_signals'}."
    )

    prompt = (
        "Summarize macro strategist view in one concise paragraph based on this regime payload: "
        f"{json.dumps(dict(quant_summary), default=str)}"
    )
    summary = _render_with_provider(
        provider,
        system_prompt="You are a macro strategist. Keep outputs concise and evidence-aware.",
        user_prompt=prompt,
        fallback=fallback_summary,
    )

    return {
        "agent": "strategist",
        "summary": summary,
        "base_case": _fallback_base_case(regime),
        "bull_case": _fallback_bull_case(regime),
        "bear_case": _fallback_bear_case(regime),
        "reason_codes": reason_codes,
        "triggers": [str(item) for item in quant_summary.get("triggers", []) if isinstance(item, str)],
    }


def build_risk_view(
    quant_summary: Mapping[str, object],
    provider: Optional[LlmProviderProtocol] = None,
) -> dict[str, object]:
    risk_flags = [str(item) for item in quant_summary.get("risk_flags", []) if isinstance(item, str)]
    fallback_summary = (
        "Risk view: "
        + (
            ", ".join(risk_flags)
            if risk_flags
            else "No acute risk flags from the current quant snapshot."
        )
    )

    prompt = (
        "Summarize macro downside risks and invalidation conditions in one concise paragraph: "
        f"{json.dumps(dict(quant_summary), default=str)}"
    )
    summary = _render_with_provider(
        provider,
        system_prompt="You are a macro risk analyst focused on downside scenarios and invalidation triggers.",
        user_prompt=prompt,
        fallback=fallback_summary,
    )

    triggers = [str(item) for item in quant_summary.get("triggers", []) if isinstance(item, str)]
    if not triggers:
        triggers = ["next_macro_release"]

    return {
        "agent": "risk",
        "summary": summary,
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
                *[str(v) for v in quant_summary.get("reason_codes", [])],
                *[str(v) for v in strategist_view.get("reason_codes", [])],
            ]
            if item
        }
    )
    risk_flags = sorted(
        {
            str(item)
            for item in [
                *[str(v) for v in quant_summary.get("risk_flags", [])],
                *[str(v) for v in risk_view.get("risk_flags", [])],
            ]
            if item
        }
    )
    triggers = sorted(
        {
            str(item)
            for item in [
                *[str(v) for v in quant_summary.get("triggers", [])],
                *[str(v) for v in strategist_view.get("triggers", [])],
                *[str(v) for v in risk_view.get("triggers", [])],
            ]
            if item
        }
    )

    return {
        "regime": regime,
        "confidence": float(quant_summary.get("confidence", 0.0)),
        "base_case": str(strategist_view.get("base_case", _fallback_base_case(regime))),
        "bull_case": str(strategist_view.get("bull_case", _fallback_bull_case(regime))),
        "bear_case": str(strategist_view.get("bear_case", _fallback_bear_case(regime))),
        "reason_codes": reason_codes,
        "risk_flags": risk_flags,
        "triggers": triggers,
        "narrative": narrative,
    }

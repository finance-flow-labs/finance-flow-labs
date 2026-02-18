import json
import os
import subprocess
from collections.abc import Mapping
from typing import Callable

from .agent_views import build_risk_view, build_strategist_view

_DEFAULT_MODEL = "gpt-5.3-codex"
_DEFAULT_TIMEOUT_SECONDS = 20
_DEFAULT_BINARY = "opencode"


def _resolve_model_name() -> str:
    raw = os.getenv("MACRO_OPENCODE_MODEL", _DEFAULT_MODEL).strip()
    return raw or _DEFAULT_MODEL


def _resolve_binary_name() -> str:
    raw = os.getenv("MACRO_OPENCODE_BIN", _DEFAULT_BINARY).strip()
    return raw or _DEFAULT_BINARY


def _resolve_timeout_seconds(timeout_seconds: int) -> int:
    if timeout_seconds <= 0:
        return _DEFAULT_TIMEOUT_SECONDS
    return timeout_seconds


def _build_strategist_prompt(quant_summary: Mapping[str, object]) -> str:
    return (
        "You are a macro strategist. Return only valid JSON with keys: "
        "summary(string), base_case(string), bull_case(string), bear_case(string), "
        "reason_codes(array of strings), triggers(array of strings), model(string). "
        "No markdown, no prose outside JSON. Quant payload: "
        f"{json.dumps(dict(quant_summary), default=str)}"
    )


def _build_risk_prompt(quant_summary: Mapping[str, object]) -> str:
    return (
        "You are a macro risk analyst. Return only valid JSON with keys: "
        "summary(string), risk_flags(array of strings), triggers(array of strings), model(string). "
        "No markdown, no prose outside JSON. Quant payload: "
        f"{json.dumps(dict(quant_summary), default=str)}"
    )


def _run_opencode(prompt: str, *, model_name: str, timeout_seconds: int) -> str:
    command = [_resolve_binary_name(), "run", "--model", model_name, prompt]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError("opencode command failed")
    return completed.stdout.strip()


def _parse_json_object(raw_output: str) -> Mapping[str, object]:
    payload = json.loads(raw_output)
    if not isinstance(payload, Mapping):
        raise ValueError("invalid JSON payload")
    return payload


def _required_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"missing string key: {key}")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"empty string key: {key}")
    return normalized


def _required_str_list(payload: Mapping[str, object], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"missing list key: {key}")

    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"invalid item type for key: {key}")
        stripped = item.strip()
        if stripped:
            normalized.append(stripped)
    return normalized


def _fallback_result(agent_name: str, quant_summary: Mapping[str, object]) -> dict[str, object]:
    view = (
        build_strategist_view(quant_summary)
        if agent_name == "strategist"
        else build_risk_view(quant_summary)
    )
    return {
        "engine": "fallback",
        "model": "deterministic-fallback",
        "view": view,
    }


def _run_agent(
    agent_name: str,
    quant_summary: Mapping[str, object],
    *,
    prompt_builder: Callable[[Mapping[str, object]], str],
    parser: Callable[[Mapping[str, object]], dict[str, object]],
    timeout_seconds: int,
) -> dict[str, object]:
    model_name = _resolve_model_name()
    resolved_timeout = _resolve_timeout_seconds(timeout_seconds)
    try:
        prompt = prompt_builder(quant_summary)
        raw_output = _run_opencode(
            prompt,
            model_name=model_name,
            timeout_seconds=resolved_timeout,
        )
        payload = _parse_json_object(raw_output)
        view = parser(payload)
        returned_model = payload.get("model")
        resolved_model = (
            returned_model.strip()
            if isinstance(returned_model, str) and returned_model.strip()
            else model_name
        )
        return {
            "engine": "opencode",
            "model": resolved_model,
            "view": view,
        }
    except (subprocess.TimeoutExpired, OSError, ValueError, json.JSONDecodeError):
        return _fallback_result(agent_name, quant_summary)


def _parse_strategist_payload(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        "agent": "strategist",
        "summary": _required_string(payload, "summary"),
        "base_case": _required_string(payload, "base_case"),
        "bull_case": _required_string(payload, "bull_case"),
        "bear_case": _required_string(payload, "bear_case"),
        "reason_codes": _required_str_list(payload, "reason_codes"),
        "triggers": _required_str_list(payload, "triggers"),
    }


def _parse_risk_payload(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        "agent": "risk",
        "summary": _required_string(payload, "summary"),
        "risk_flags": _required_str_list(payload, "risk_flags"),
        "triggers": _required_str_list(payload, "triggers"),
    }


def generate_strategist_view(
    quant_summary: Mapping[str, object],
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, object]:
    return _run_agent(
        "strategist",
        quant_summary,
        prompt_builder=_build_strategist_prompt,
        parser=_parse_strategist_payload,
        timeout_seconds=timeout_seconds,
    )


def generate_risk_view(
    quant_summary: Mapping[str, object],
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, object]:
    return _run_agent(
        "risk",
        quant_summary,
        prompt_builder=_build_risk_prompt,
        parser=_parse_risk_payload,
        timeout_seconds=timeout_seconds,
    )

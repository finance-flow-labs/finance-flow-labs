import importlib


streamlit_access = importlib.import_module("src.ingestion.streamlit_access")


def test_check_streamlit_access_detects_auth_wall_from_final_url():
    def fake_fetch(url: str, timeout_seconds: float):
        return (
            200,
            "https://share.streamlit.io/-/auth/app?redirect_uri=https%3A%2F%2Ffinance-flow-labs.streamlit.app%2F",
            {},
            "",
        )

    result = streamlit_access.check_streamlit_access(
        "https://finance-flow-labs.streamlit.app/",
        fetch=fake_fetch,
    )

    assert result.ok is False
    assert result.auth_wall_redirect is True
    assert result.reason == "auth_wall_redirect_detected"


def test_check_streamlit_access_detects_auth_wall_from_location_header():
    def fake_fetch(url: str, timeout_seconds: float):
        return (
            303,
            "https://finance-flow-labs.streamlit.app/",
            {
                "Location": "https://share.streamlit.io/-/auth/app?redirect_uri=https%3A%2F%2Ffinance-flow-labs.streamlit.app%2F"
            },
            "",
        )

    result = streamlit_access.check_streamlit_access(
        "https://finance-flow-labs.streamlit.app/",
        fetch=fake_fetch,
    )

    assert result.ok is False
    assert result.auth_wall_redirect is True


def test_check_streamlit_access_detects_streamlit_login_redirect_loop():
    def fake_fetch(url: str, timeout_seconds: float):
        return (
            303,
            "https://finance-flow-labs.streamlit.app/-/login?payload=abc123",
            {},
            "",
        )

    result = streamlit_access.check_streamlit_access(
        "https://finance-flow-labs.streamlit.app/",
        fetch=fake_fetch,
    )

    assert result.ok is False
    assert result.auth_wall_redirect is True
    assert result.reason == "auth_wall_redirect_detected"


def test_check_streamlit_access_accepts_streamlit_shell_response():
    def fake_fetch(url: str, timeout_seconds: float):
        return (
            200,
            "https://finance-flow-labs.streamlit.app/",
            {},
            "<!doctype html><title>Streamlit</title>",
        )

    result = streamlit_access.check_streamlit_access(
        "https://finance-flow-labs.streamlit.app/",
        fetch=fake_fetch,
    )

    assert result.ok is True
    assert result.reason == "ok"


def test_check_streamlit_access_flags_non_shell_payload_as_unexpected():
    def fake_fetch(url: str, timeout_seconds: float):
        return (200, "https://finance-flow-labs.streamlit.app/", {}, "plain text")

    result = streamlit_access.check_streamlit_access(
        "https://finance-flow-labs.streamlit.app/",
        fetch=fake_fetch,
    )

    assert result.ok is False
    assert result.auth_wall_redirect is False
    assert result.reason == "unexpected_response"


def test_check_streamlit_access_retries_transient_network_error_then_succeeds():
    calls: list[int] = []

    def fake_fetch(url: str, timeout_seconds: float):
        calls.append(1)
        if len(calls) == 1:
            raise streamlit_access.URLError("temporary_dns_failure")
        return (200, url, {}, "<html>streamlit</html>")

    result = streamlit_access.check_streamlit_access(
        "https://finance-flow-labs.streamlit.app/",
        fetch=fake_fetch,
        attempts=2,
        backoff_seconds=0,
    )

    assert len(calls) == 2
    assert result.ok is True
    assert result.reason == "ok"


def test_check_streamlit_access_does_not_retry_auth_wall_failures():
    calls: list[int] = []

    def fake_fetch(url: str, timeout_seconds: float):
        calls.append(1)
        return (
            303,
            "https://share.streamlit.io/-/auth/app?redirect_uri=https%3A%2F%2Ffinance-flow-labs.streamlit.app%2F",
            {},
            "",
        )

    result = streamlit_access.check_streamlit_access(
        "https://finance-flow-labs.streamlit.app/",
        fetch=fake_fetch,
        attempts=5,
        backoff_seconds=0,
    )

    assert len(calls) == 1
    assert result.ok is False
    assert result.reason == "auth_wall_redirect_detected"


def test_access_check_result_serializes_alert_fields():
    result = streamlit_access.AccessCheckResult(
        ok=False,
        status_code=303,
        final_url="https://finance-flow-labs.streamlit.app/",
        auth_wall_redirect=True,
        reason="auth_wall_redirect_detected",
    )

    payload = result.to_dict()

    assert payload["alert"] is True
    assert payload["alert_severity"] == "critical"

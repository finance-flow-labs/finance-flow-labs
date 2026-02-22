import importlib


deploy_access_policy = importlib.import_module("src.ingestion.deploy_access_policy")


def test_public_mode_blocks_auth_wall_redirect():
    decision = deploy_access_policy.evaluate_deploy_access(
        {
            "ok": False,
            "auth_wall_redirect": True,
            "reason": "auth_wall_redirect_detected",
        },
        mode="public",
    )

    assert decision.ok is False
    assert decision.release_blocker is True
    assert decision.reason == "auth_wall_redirect_detected"


def test_restricted_mode_allows_auth_wall_with_documented_login_path():
    decision = deploy_access_policy.evaluate_deploy_access(
        {
            "ok": False,
            "auth_wall_redirect": True,
            "reason": "auth_wall_redirect_detected",
        },
        mode="restricted",
        restricted_login_path="https://share.streamlit.io/login",
    )

    assert decision.ok is True
    assert decision.release_blocker is False
    assert decision.reason == "restricted_auth_required"


def test_restricted_mode_requires_documented_login_path_for_auth_wall():
    decision = deploy_access_policy.evaluate_deploy_access(
        {
            "ok": False,
            "auth_wall_redirect": True,
            "reason": "auth_wall_redirect_detected",
        },
        mode="restricted",
        restricted_login_path=None,
    )

    assert decision.ok is False
    assert decision.release_blocker is True
    assert decision.reason == "restricted_mode_login_path_missing"

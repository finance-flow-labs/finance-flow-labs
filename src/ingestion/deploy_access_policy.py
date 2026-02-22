from __future__ import annotations

from dataclasses import dataclass


ALLOWED_MODES = {"public", "restricted"}


@dataclass(frozen=True)
class DeployAccessDecision:
    ok: bool
    mode: str
    release_blocker: bool
    reason: str
    severity: str
    operator_message: str

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "release_blocker": self.release_blocker,
            "reason": self.reason,
            "severity": self.severity,
            "operator_message": self.operator_message,
        }


def normalize_access_mode(mode: str | None) -> str:
    normalized = (mode or "public").strip().lower()
    if normalized not in ALLOWED_MODES:
        raise ValueError(f"DEPLOY_ACCESS_MODE must be one of {sorted(ALLOWED_MODES)}")
    return normalized


def evaluate_deploy_access(
    access_result: dict[str, object],
    *,
    mode: str,
    restricted_login_path: str | None = None,
) -> DeployAccessDecision:
    access_mode = normalize_access_mode(mode)

    ok = bool(access_result.get("ok"))
    auth_wall_redirect = bool(access_result.get("auth_wall_redirect"))
    reason = str(access_result.get("reason") or "unknown")

    if access_mode == "public":
        if ok:
            return DeployAccessDecision(
                ok=True,
                mode=access_mode,
                release_blocker=False,
                reason="ok",
                severity="none",
                operator_message="Public mode validated: dashboard shell reachable without auth wall.",
            )

        severity = "critical" if auth_wall_redirect else "warning"
        return DeployAccessDecision(
            ok=False,
            mode=access_mode,
            release_blocker=True,
            reason=reason,
            severity=severity,
            operator_message=(
                "Public mode violation: unauthenticated dashboard access failed. "
                "Set Streamlit visibility to Public, redeploy, and rerun gate."
            ),
        )

    # restricted mode
    if ok:
        return DeployAccessDecision(
            ok=True,
            mode=access_mode,
            release_blocker=False,
            reason="ok",
            severity="none",
            operator_message="Restricted mode validated with reachable dashboard shell.",
        )

    if auth_wall_redirect and restricted_login_path:
        return DeployAccessDecision(
            ok=True,
            mode=access_mode,
            release_blocker=False,
            reason="restricted_auth_required",
            severity="info",
            operator_message=(
                "Restricted mode active: auth wall detected as expected. "
                f"Operator login path: {restricted_login_path}"
            ),
        )

    return DeployAccessDecision(
        ok=False,
        mode=access_mode,
        release_blocker=True,
        reason="restricted_mode_login_path_missing" if auth_wall_redirect else reason,
        severity="critical" if auth_wall_redirect else "warning",
        operator_message=(
            "Restricted mode requires documented operator login path when auth wall is detected."
            if auth_wall_redirect
            else "Restricted mode check failed for non-auth-wall reason. Investigate deployment health."
        ),
    )

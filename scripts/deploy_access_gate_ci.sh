#!/usr/bin/env bash
set -euo pipefail

URL="${1:-https://finance-flow-labs.streamlit.app/}"
MODE="${DEPLOY_ACCESS_MODE:-public}"
LOGIN_PATH="${DEPLOY_RESTRICTED_LOGIN_PATH:-}"

TMP_JSON="$(mktemp)"
cleanup() {
  rm -f "$TMP_JSON"
}
trap cleanup EXIT

python3 -m src.ingestion.cli deploy-access-gate \
  --url "$URL" \
  --mode "$MODE" \
  ${LOGIN_PATH:+--restricted-login-path "$LOGIN_PATH"} >"$TMP_JSON"

cat "$TMP_JSON"

python3 - "$TMP_JSON" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
access = payload.get("access_check", {})
gate = payload.get("gate", {})

reason = str(gate.get("reason") or access.get("reason") or "unknown")
severity = str(gate.get("severity") or access.get("alert_severity") or "unknown")
hint = str(gate.get("remediation_hint") or access.get("remediation_hint") or "")
release_blocker = bool(gate.get("release_blocker"))
mode = str(payload.get("deploy_access_mode") or "public")

print(f"[deploy-access-gate] mode={mode} release_blocker={release_blocker} reason={reason} severity={severity}")
if hint:
    print(f"[deploy-access-gate] hint={hint}")

summary_path = Path("deploy_access_gate_summary.md")
summary_path.write_text(
    "\n".join(
        [
            "## Deploy Access Gate",
            f"- mode: `{mode}`",
            f"- release_blocker: `{str(release_blocker).lower()}`",
            f"- reason: `{reason}`",
            f"- severity: `{severity}`",
            f"- hint: {hint or '(none)' }",
        ]
    )
    + "\n",
    encoding="utf-8",
)

if release_blocker:
    sys.exit(2)
PY
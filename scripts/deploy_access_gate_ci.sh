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

python3 - "$URL" "$MODE" "$LOGIN_PATH" "$TMP_JSON" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

url = sys.argv[1]
mode = sys.argv[2]
login_path = sys.argv[3]
out_path = Path(sys.argv[4])

routes = [
    ("default", url),
    ("enduser", f"{url}?view=enduser"),
    ("operator", f"{url}?view=operator"),
]

results: list[dict[str, object]] = []
release_blocker = False

for label, route_url in routes:
    cmd = [
        "python3",
        "-m",
        "src.ingestion.cli",
        "deploy-access-gate",
        "--url",
        route_url,
        "--mode",
        mode,
    ]
    if login_path:
        cmd += ["--restricted-login-path", login_path]

    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    payload = json.loads(proc.stdout)

    access = payload.get("access_check", {})
    gate = payload.get("gate", {})
    reason = str(gate.get("reason") or access.get("reason") or "unknown")
    severity = str(gate.get("severity") or access.get("alert_severity") or "unknown")
    hint = str(gate.get("remediation_hint") or access.get("remediation_hint") or "")
    is_blocker = bool(gate.get("release_blocker"))
    release_blocker = release_blocker or is_blocker

    print(
        f"[deploy-access-gate:{label}] mode={mode} release_blocker={is_blocker} reason={reason} severity={severity}"
    )
    if hint:
        print(f"[deploy-access-gate:{label}] hint={hint}")

    results.append(
        {
            "route": label,
            "url": route_url,
            "release_blocker": is_blocker,
            "reason": reason,
            "severity": severity,
            "hint": hint,
        }
    )

summary_lines = ["## Deploy Access Gate", f"- mode: `{mode}`", "- routes:"]
for item in results:
    summary_lines.append(
        "  - "
        + f"{item['route']}: blocker=`{str(item['release_blocker']).lower()}` "
        + f"reason=`{item['reason']}` severity=`{item['severity']}`"
    )
    if item["hint"]:
        summary_lines.append(f"    - hint: {item['hint']}")

Path("deploy_access_gate_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

if release_blocker:
    raise SystemExit(2)
PY

cat "$TMP_JSON"

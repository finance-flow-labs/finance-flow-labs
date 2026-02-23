#!/usr/bin/env bash
set -euo pipefail

URL="${1:-https://finance-flow-labs.streamlit.app/}"

check_route() {
  local route_url="$1"
  local label="$2"

  echo "[post-deploy-verify] streamlit access contract check (${label}): ${route_url}"
  if ./scripts/streamlit_access_smoke_check.sh "$route_url"; then
    return 0
  fi

  echo "[post-deploy-verify] failed route: ${label}"
  return 1
}

failures=0

check_route "$URL" "default" || failures=$((failures + 1))
check_route "${URL}?view=enduser" "enduser" || failures=$((failures + 1))
check_route "${URL}?view=operator" "operator" || failures=$((failures + 1))

if [[ "$failures" -gt 0 ]]; then
  echo "[post-deploy-verify] failed (${failures} route(s))"
  exit 1
fi

echo "[post-deploy-verify] ok"

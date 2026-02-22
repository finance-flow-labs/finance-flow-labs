#!/usr/bin/env bash
set -euo pipefail

URL="${1:-https://finance-flow-labs.streamlit.app/}"

check_route() {
  local route_url="$1"
  local label="$2"

  echo "[post-deploy-verify] streamlit access contract check (${label}): ${route_url}"
  ./scripts/streamlit_access_smoke_check.sh "$route_url"
}

check_route "$URL" "default"
check_route "${URL}?view=enduser" "enduser"
check_route "${URL}?view=operator" "operator"

echo "[post-deploy-verify] ok"

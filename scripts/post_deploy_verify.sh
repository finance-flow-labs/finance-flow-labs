#!/usr/bin/env bash
set -euo pipefail

URL="${1:-https://finance-flow-labs.streamlit.app/}"

echo "[post-deploy-verify] streamlit access contract check: $URL"
./scripts/streamlit_access_smoke_check.sh "$URL"

echo "[post-deploy-verify] ok"

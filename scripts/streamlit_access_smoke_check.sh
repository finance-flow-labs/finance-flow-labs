#!/usr/bin/env bash
set -euo pipefail

URL="${1:-https://finance-flow-labs.streamlit.app/}"
ATTEMPTS="${ATTEMPTS:-3}"
BACKOFF_SECONDS="${BACKOFF_SECONDS:-0.5}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-15}"
DEPLOY_ACCESS_MODE="${DEPLOY_ACCESS_MODE:-public}"
DEPLOY_RESTRICTED_LOGIN_PATH="${DEPLOY_RESTRICTED_LOGIN_PATH:-}"

cmd=(
  python3 -m src.ingestion.cli deploy-access-gate
  --url "$URL"
  --mode "$DEPLOY_ACCESS_MODE"
  --attempts "$ATTEMPTS"
  --backoff-seconds "$BACKOFF_SECONDS"
  --timeout-seconds "$TIMEOUT_SECONDS"
)

if [[ -n "$DEPLOY_RESTRICTED_LOGIN_PATH" ]]; then
  cmd+=(--restricted-login-path "$DEPLOY_RESTRICTED_LOGIN_PATH")
fi

"${cmd[@]}"

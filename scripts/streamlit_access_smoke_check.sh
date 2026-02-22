#!/usr/bin/env bash
set -euo pipefail

URL="${1:-https://finance-flow-labs.streamlit.app/}"
ATTEMPTS="${ATTEMPTS:-3}"
BACKOFF_SECONDS="${BACKOFF_SECONDS:-0.5}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-15}"

python3 -m src.ingestion.cli streamlit-access-check \
  --url "$URL" \
  --attempts "$ATTEMPTS" \
  --backoff-seconds "$BACKOFF_SECONDS" \
  --timeout-seconds "$TIMEOUT_SECONDS"

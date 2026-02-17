# Ingestion Runbook

## Core Flow

1. Evaluate source with legal/reliability hard gates.
2. Ingest raw payloads into append-only raw store.
3. Run quality gate checks.
4. Promote passing batches to canonical facts.
5. Route failing batches to quarantine.
6. Serve research queries with point-in-time filters.

## Safety Rules

- Never overwrite historical raw records.
- Enforce `available_at <= decision_time` for replay and backtesting.
- Freeze new source onboarding if monthly budget is exceeded.

## Tier Policy

- Gold: no TTL expiration.
- Silver: 180-day raw cache, 24-month facts.
- Bronze: 30-90 day cache window.

## Manual Update

- SEC run: `python3 -m src.ingestion.cli run-update --source sec_edgar`
- FRED run: `python3 -m src.ingestion.cli run-update --source fred`
- DART run: `python3 -m src.ingestion.cli run-update --source opendart`
- ECOS run: `python3 -m src.ingestion.cli run-update --source ecos`

Environment variables:

- `SUPABASE_DB_URL` or `DATABASE_URL` for run history persistence
- `SEC_USER_AGENT` and optional `SEC_CIK` for SEC source
- `FRED_API_KEY` and optional `FRED_SERIES_ID` for FRED source
- `DART_API_KEY` or `DART_CRTFC_KEY` and optional `DART_CORP_CODE` for DART source
- `ECOS_API_KEY` and optional `ECOS_STAT_CODE` for ECOS source

## Operator Dashboard

- Run: `streamlit run src/dashboard/app.py`
- Required: `SUPABASE_DB_URL` or `DATABASE_URL`
- Dashboard shows:
  - last run status/time
  - raw/canonical/quarantine counters
  - recent run history

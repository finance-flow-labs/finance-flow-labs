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

## Normalization (v1)

- 목적: 소스별 raw payload(FRED/ECOS)를 분석 공통 포맷으로 정규화
- 정규화 포인트 스키마:
  - `source`, `entity_id`, `metric_key`, `as_of`, `available_at`, `value`, `lineage_id`
- 저장 테이블: `macro_series_points` (`migrations/004_macro_series_points.sql`)
- Repository API:
  - `write_macro_series_points(points)`
  - `read_macro_series_points(metric_key, limit)`
- 동작 규칙:
  - `run_ingestion_job()`에서 FRED/ECOS 배치가 canonical로 승격되면 정규화 후 `macro_series_points`를 자동 적재
  - 품질/소스 게이트 실패로 quarantine된 배치는 정규화 적재를 수행하지 않음

## Macro Analysis Persistence (v1)

- LLM/agent 기반 매크로 분석 결과 저장 테이블: `macro_analysis_results`
- 마이그레이션: `migrations/005_macro_analysis_results.sql`
- Repository API:
  - `write_macro_analysis_result(result)`
  - `read_latest_macro_analysis(limit)`
- 저장 필드에는 `regime`, `confidence`, `base/bull/bear`, `policy_case`, `critic_case`, `reason_codes`, `risk_flags`, `triggers`, `narrative`, `model` 포함

## Forecast Capture (operator-safe)

Use CLI (no direct SQL) to create/update a forecast record with schema validation and idempotency (`thesis_id + horizon + as_of`).

Example:

```bash
python3 -m src.ingestion.cli forecast-record-create \
  --thesis-id thesis-aapl-2026q1 \
  --horizon 1M \
  --expected-return-low 0.03 \
  --expected-return-high 0.09 \
  --expected-volatility 0.20 \
  --expected-drawdown 0.12 \
  --confidence 0.68 \
  --key-drivers-json '["macro:disinflation","sector:semis"]' \
  --evidence-hard-json '[{"source":"fred","metric":"CPI","as_of":"2026-02-20"}]' \
  --evidence-soft-json '[{"source":"news","note":"earnings-call tone improved"}]' \
  --as-of 2026-02-22T00:00:00+00:00
```

Validation guardrails:
- `expected_return_low <= expected_return_high`
- `confidence` must be between `0` and `1`
- `--as-of` must be timezone-aware ISO-8601
- `--evidence-hard-json` must be non-empty JSON array (HARD evidence required)

## Operator Dashboard

- Run: `streamlit run src/dashboard/app.py`
- Required: `SUPABASE_DB_URL` or `DATABASE_URL`
- Dashboard shows:
  - last run status/time
  - raw/canonical/quarantine counters
  - multi-horizon learning metrics with reliability guardrails (`insufficient` / `low_sample` / `reliable`)
    - reliability badges: `🔴 insufficient`, `🟠 low_sample`, `🟢 reliable`
    - each row includes a human-readable reliability reason to prevent over-trusting sparse KPI samples
  - recent run history
- Reliability threshold env overrides:
  - `LEARNING_RELIABILITY_MIN_REALIZED_1W` (default: `8`)
  - `LEARNING_RELIABILITY_MIN_REALIZED_1M` (default: `12`)
  - `LEARNING_RELIABILITY_MIN_REALIZED_3M` (default: `6`)
  - `LEARNING_RELIABILITY_COVERAGE_FLOOR` (default: `0.4`)

### Streamlit Community Cloud Deployment

1. Go to `https://share.streamlit.io` and sign in with GitHub.
2. Click `Create app`.
3. Select repository: `finance-flow-labs/finance-flow-labs`.
4. Select branch: `main`.
5. Set Main file path: `streamlit_app.py`.
6. Set Secret: `SUPABASE_DB_URL` (or `DATABASE_URL`).
7. Deploy and copy the generated app URL (`https://<app-name>.streamlit.app`).

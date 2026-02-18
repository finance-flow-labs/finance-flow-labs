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

## Macro Analysis Persistence (v1)

- LLM/agent 기반 매크로 분석 결과 저장 테이블: `macro_analysis_results`
- 마이그레이션: `migrations/005_macro_analysis_results.sql`
- Repository API:
  - `write_macro_analysis_result(result)`
  - `read_latest_macro_analysis(limit)`
- 저장 필드에는 `regime`, `confidence`, `base/bull/bear`, `reason_codes`, `risk_flags`, `triggers`, `narrative`, `model` 포함

## Macro Analysis Runner (multi-agent + fallback)

- 사전 조건:
  - `migrations/004_macro_series_points.sql` 및 `migrations/005_macro_analysis_results.sql` 적용
- CLI 실행:
  - `python3 -m src.ingestion.cli run-macro-analysis`
  - 특정 지표 지정: `python3 -m src.ingestion.cli run-macro-analysis --metric-key CPIAUCSL --metric-key KOR_BASE_RATE`
  - 시점/윈도우 지정: `python3 -m src.ingestion.cli run-macro-analysis --as-of 2026-02-18T00:00:00+00:00 --limit 120`
  - deterministic 강제 모드: `python3 -m src.ingestion.cli run-macro-analysis --analysis-engine fallback`
- 내부 단계:
  1. Quant signal 산출 (`macro_series_points` 조회)
  2. Strategist view 생성 (OpenCode CLI 또는 deterministic fallback)
  3. Risk view 생성 (OpenCode CLI 또는 deterministic fallback)
  4. Synthesis 후 `macro_analysis_results` 저장
- LLM fallback 정책:
  - 기본 엔진은 `opencode`이며 OpenCode CLI를 호출해 strategist/risk JSON 응답을 생성
  - CLI 응답이 timeout/파싱 실패/비정상 종료면 deterministic 템플릿으로 자동 fallback
  - 강제 fallback 모드는 `--analysis-engine fallback`
  - 요약 출력에 `engine`/`model`이 포함되며, fallback 시 model은 `deterministic-fallback`
  - fallback 모드에서도 `regime/confidence/base/bull/bear/reason_codes/risk_flags/triggers/narrative/model` 모두 저장

## Operator Dashboard

- Run: `streamlit run src/dashboard/app.py`
- Required: `SUPABASE_DB_URL` or `DATABASE_URL`
- Dashboard shows:
  - last run status/time
  - raw/canonical/quarantine counters
  - recent run history

### Streamlit Community Cloud Deployment

1. Go to `https://share.streamlit.io` and sign in with GitHub.
2. Click `Create app`.
3. Select repository: `finance-flow-labs/finance-flow-labs`.
4. Select branch: `main`.
5. Set Main file path: `streamlit_app.py`.
6. Set Secret: `SUPABASE_DB_URL` (or `DATABASE_URL`).
7. Deploy and copy the generated app URL (`https://<app-name>.streamlit.app`).

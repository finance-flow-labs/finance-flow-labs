# Macro-to-Stock Flow Status (2026-02-18)

## Original Target Flow

1. Data collection
2. Macro analysis
3. Sector recommendation
4. Sector analysis
5. Stock recommendation
6. Stock analysis

## Current Status Summary

| Stage | Status | Evidence |
|---|---|---|
| 1) Data collection | Implemented (v1 ingestion) | `src/ingestion/cli.py`, `src/ingestion/job.py`, adapters in `src/ingestion/adapters/`, migrations in `migrations/` |
| 2) Macro analysis | Not implemented (data source only) | Macro sources exist in docs/catalog, but no macro signal/model module in `src/` |
| 3) Sector recommendation | Not implemented | No sector ranking/recommendation engine in `src/`/`tests/` |
| 4) Sector analysis | Not implemented | No sector scoring/factor analysis module in `src/`/`tests/` |
| 5) Stock recommendation | Not implemented | No stock screener/ranking/recommendation logic in `src/`/`tests/` |
| 6) Stock analysis | Not implemented | No stock-level valuation/risk/decision packet module in `src/`/`tests/` |

## What Is Actually Completed

### A. Ingestion and storage pipeline

- Source fetch/update command path is implemented (`run-update`):
  - `src/ingestion/cli.py`
- Ingestion execution path with source gate + quality gate + quarantine/canonical routing:
  - `src/ingestion/job.py`
  - `src/ingestion/source_registry.py`
  - `src/ingestion/quality_gate.py`
- KR+US adapter fetch implementations for v1:
  - `src/ingestion/adapters/sec_edgar.py`
  - `src/ingestion/adapters/opendart.py`
  - `src/ingestion/adapters/fred.py`
  - `src/ingestion/adapters/ecos.py`
- Storage models and migrations:
  - `migrations/001_raw_event_store.sql`
  - `migrations/002_canonical_and_quarantine.sql`
  - `migrations/003_ingestion_runs.sql`
  - `src/ingestion/postgres_repository.py`

### B. Operator operations and visibility

- Manual run orchestration and run-history record:
  - `src/ingestion/manual_runner.py`
- Operator dashboard view-model and UI:
  - `src/ingestion/dashboard_service.py`
  - `src/dashboard/app.py`
  - `streamlit_app.py`

### C. Validation coverage around ingestion

- Ingestion/pipeline/adapters/dashboard smoke and unit tests exist:
  - `tests/test_ingestion_job.py`
  - `tests/test_end_to_end_ingestion.py`
  - `tests/test_adapter_fetch.py`
  - `tests/test_adapters_contract.py`
  - `tests/test_manual_runner.py`
  - `tests/test_dashboard_service.py`
  - `tests/test_dashboard_app_smoke.py`

## Gap Assessment Against the Original Flow

The current codebase is strong on data plumbing (collect/store/monitor), but does not yet contain executable intelligence modules for:

- macro regime inference
- sector ranking/recommendation
- sector deep-dive analytics
- stock ranking/recommendation
- stock-level decision analysis

The phrase "macro -> sector -> stock" appears as use-case intent in design docs, but the executable implementation currently stops at ingestion and operator monitoring.

## Proposed Next Build Sequence

1. `macro_analysis` module
   - Input: canonical macro/fundamental series
   - Output: time-stamped macro regime + confidence + rationale fields
2. `sector_recommendation` module
   - Input: macro regime outputs
   - Output: ranked sectors (top-N, score, confidence)
3. `sector_analysis` module
   - Input: selected sectors + factor datasets
   - Output: sector-level analytic report artifacts
4. `stock_recommendation` module
   - Input: selected sectors + stock universe features
   - Output: ranked stock candidates + rejection reasons
5. `stock_analysis` module
   - Input: recommended stock list + fundamentals/price/history
   - Output: stock decision packet (thesis, risk, trigger, uncertainty)

## Definition of Done for Each Future Stage

A stage is considered complete only when all are present:

1. Executable module in `src/`
2. Test coverage in `tests/`
3. Runbook/docs describing inputs/outputs and validation policy
4. Persisted outputs (table/schema/log) with reproducible timestamped records

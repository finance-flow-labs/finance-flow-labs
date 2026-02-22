-- Migration 008: Create stock_analysis_results table
-- Stores multi-agent stock analysis results for individual equities.
-- Supports both Korean (DART) and US (SEC EDGAR) markets.

CREATE TABLE IF NOT EXISTS stock_analysis_results (
    id              BIGSERIAL PRIMARY KEY,
    run_id          TEXT        NOT NULL,
    ticker          TEXT        NOT NULL,
    company_name    TEXT,
    market          TEXT,                           -- 'KR' or 'US'
    as_of           TIMESTAMPTZ NOT NULL,           -- analysis reference date/time
    bull_case       TEXT        NOT NULL DEFAULT '',
    bear_case       TEXT        NOT NULL DEFAULT '',
    fundamental_case TEXT       NOT NULL DEFAULT '',
    value_case      TEXT        NOT NULL DEFAULT '',
    growth_case     TEXT        NOT NULL DEFAULT '',
    risk_case       TEXT        NOT NULL DEFAULT '',
    critic_case     TEXT        NOT NULL DEFAULT '',
    narrative       TEXT        NOT NULL DEFAULT '',
    model           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast lookup by ticker ordered by most recent analysis
CREATE INDEX IF NOT EXISTS idx_stock_analysis_ticker_as_of
    ON stock_analysis_results (ticker, as_of DESC, created_at DESC);

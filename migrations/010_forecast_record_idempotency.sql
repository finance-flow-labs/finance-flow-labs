CREATE UNIQUE INDEX IF NOT EXISTS uq_forecast_records_thesis_horizon_as_of
ON forecast_records(thesis_id, horizon, as_of);

ALTER TABLE macro_analysis_results
ADD COLUMN IF NOT EXISTS evidence_hard JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE macro_analysis_results
ADD COLUMN IF NOT EXISTS evidence_soft JSONB NOT NULL DEFAULT '[]'::jsonb;

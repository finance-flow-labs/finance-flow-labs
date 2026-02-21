ALTER TABLE macro_analysis_results
ADD COLUMN IF NOT EXISTS policy_case TEXT NOT NULL DEFAULT '';

ALTER TABLE macro_analysis_results
ADD COLUMN IF NOT EXISTS critic_case TEXT NOT NULL DEFAULT '';

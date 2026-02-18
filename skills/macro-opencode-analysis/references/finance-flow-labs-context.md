# Finance Flow Labs Context

## Key Files

- `src/research/macro_analysis.py` - quant signal calculation
- `src/research/agent_views.py` - deterministic synthesis payload shaping
- `src/research/opencode_runner.py` - OpenCode CLI execution and response parsing
- `src/research/flow_runner.py` - quant → views → synthesis → persistence orchestration
- `src/ingestion/cli.py` - `run-macro-analysis` command wiring
- `src/ingestion/postgres_repository.py` - persistence read/write methods

## Persistence Tables

- `macro_series_points`
  - migration: `migrations/004_macro_series_points.sql`
- `macro_analysis_results`
  - migration: `migrations/005_macro_analysis_results.sql`

## Existing Tests to Extend

- `tests/test_macro_analysis_pipeline.py`
- `tests/test_macro_analysis_cli.py`
- `tests/test_macro_analysis_repository.py`
- `tests/test_cli_smoke.py`

## Verification Commands

```bash
PYTHONPATH=. pytest -q
```

Optional targeted runs:

```bash
PYTHONPATH=. pytest -q tests/test_macro_analysis_pipeline.py
PYTHONPATH=. pytest -q tests/test_macro_analysis_cli.py
```

## Architecture Constraints

- Keep direct provider HTTP code out of app logic.
- Treat OpenCode runner as execution boundary for generated analysis text.
- Keep deterministic fallback fully functional and test-covered.

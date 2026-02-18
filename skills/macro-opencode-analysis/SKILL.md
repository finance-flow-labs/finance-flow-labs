---
name: macro-opencode-analysis
description: Build or update finance-flow-labs macro analysis features through OpenCode agent execution (Codex xhigh), including quant signals, strategist/risk synthesis, DB persistence, CLI wiring, and dashboard exposure. Use when implementing macro analysis behavior and enforcing no direct OpenAI HTTP calls in application code.
---

# Macro OpenCode Analysis

## Overview

Use this skill to implement macro analysis features in `finance-flow-labs` with an OpenCode-agent workflow.

Keep application code free of direct OpenAI HTTP requests. Generate analysis text through OpenCode execution path or deterministic fallback.

## Non-Negotiable Rules

- Use OpenCode for implementation runs.
- Use Codex xhigh for OpenCode executions.
- Do not add direct OpenAI API calls (`urllib`/`requests` to OpenAI endpoints) in app code.
- Implement one feature unit per PR and share PR URL.

## Quick Start

1. Read `references/finance-flow-labs-context.md`.
2. If prompt quality is drifting, use `references/opencode-prompt-template.md`.
3. Implement one scoped feature slice.
4. Run verification (`PYTHONPATH=. pytest -q` + targeted smoke).
5. Commit and open PR.

## Implementation Workflow

### 1) Scope a Single Feature Slice

Pick exactly one of:
- Quant signal logic update
- Strategist/risk generation path update
- Persistence schema/repository update
- CLI option/runner update
- Dashboard section update

### 2) Preserve Layer Boundaries

- `src/research/macro_analysis.py`: quant logic only
- `src/research/agent_views.py`: deterministic synthesis and shaping
- `src/research/opencode_runner.py`: OpenCode invocation and JSON parsing/fallback handling
- `src/research/flow_runner.py`: orchestration and persistence handoff
- `src/ingestion/cli.py`: command interface only

### 3) Enforce No Direct OpenAI Calls

Before and after edits, check:

```bash
grep -RIn "api.openai.com\|chat/completions\|responses" src
```

Result should be empty for application flow files.

### 4) Test and Verify

Run:

```bash
PYTHONPATH=. pytest -q
```

For CLI changes, include a smoke command in PR notes.

## PR Standard

Every feature PR should include:
- What changed (module-level summary)
- Why this preserves OpenCode-agent architecture
- Test result (`PYTHONPATH=. pytest -q`)
- Any migration/manual steps

## References

- For repository structure, contracts, and command patterns: `references/finance-flow-labs-context.md`
- For OpenCode execution prompt structure: `references/opencode-prompt-template.md`

## Common Mistakes

- Mixing orchestration logic into `cli.py`
- Adding direct provider HTTP client back into app code
- Bundling multiple feature slices into one PR
- Skipping fallback-path tests for runner failures

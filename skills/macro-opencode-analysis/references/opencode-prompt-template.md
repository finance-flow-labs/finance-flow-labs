# OpenCode Prompt Template (Macro Analysis)

Use this template when OpenCode drifts into planning loops.

```text
Implement directly now. Do not use task() or subagents. Do not enter planning mode.

Target branch: <branch-name>
Scope: <single feature slice>

Requirements:
1) <file-level changes>
2) <tests to add/update>
3) <docs to update>

Constraints:
- Use model openai/gpt-5.3-codex and variant xhigh.
- Keep app code free of direct OpenAI HTTP calls.
- Keep deterministic fallback path.

Validation:
- Run: PYTHONPATH=. pytest -q
- Commit: <commit-message>

Output exactly:
SUMMARY
CHANGED_FILES
TEST_RESULT
COMMIT_SHA
```

## Recommended CLI Form

```bash
opencode run -m openai/gpt-5.3-codex --variant xhigh "<prompt above>"
```

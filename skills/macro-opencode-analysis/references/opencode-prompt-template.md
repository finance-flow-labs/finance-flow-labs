# OpenCode 프롬프트 템플릿 (매크로 분석)

OpenCode가 플래닝 루프에 빠질 때 아래 템플릿을 사용한다.

## REQUIRED 슈퍼파워 스킬 세트

아래 5개는 항상 함께 명시한다.

- `superpowers/using-superpowers`
- `superpowers/writing-plans`
- `superpowers/test-driven-development`
- `superpowers/verification-before-completion`
- `superpowers/requesting-code-review`

슈퍼파워 스킬 누락 시 구현을 시작하지 마라.

```text
바로 구현해라. task() 또는 서브에이전트를 사용하지 마라. planning 모드로 들어가지 마라.

REQUIRED 슈퍼파워 스킬 세트: superpowers/using-superpowers, superpowers/writing-plans, superpowers/test-driven-development, superpowers/verification-before-completion, superpowers/requesting-code-review
각 스킬을 먼저 호출한 뒤 구현을 시작해라.

대상 브랜치: <branch-name>
범위: <single feature slice>

요구사항:
1) <file-level changes>
2) <tests to add/update>
3) <docs to update>

제약:
- 모델은 openai/gpt-5.3-codex, variant는 xhigh를 사용한다.
- 앱 코드에 직접 OpenAI HTTP 호출을 넣지 않는다.
- 결정론적 fallback 경로를 유지한다.

검증:
- 실행: PYTHONPATH=. pytest -q
- 커밋: <commit-message>

마지막 출력 형식(정확히):
SUMMARY
CHANGED_FILES
TEST_RESULT
COMMIT_SHA
```

## 권장 CLI 형태

```bash
opencode run -m openai/gpt-5.3-codex --variant xhigh "REQUIRED 슈퍼파워 스킬 세트를 포함한 <위 템플릿 프롬프트>"
```

## OpenCode 명령 예시(슈퍼파워 사용 가이드 포함)

```bash
opencode run -m openai/gpt-5.3-codex --variant xhigh "REQUIRED 슈퍼파워 스킬 세트: superpowers/using-superpowers, superpowers/writing-plans, superpowers/test-driven-development, superpowers/verification-before-completion, superpowers/requesting-code-review. 각 스킬을 먼저 호출한 뒤 구현을 시작해라. 슈퍼파워 스킬 누락 시 구현을 시작하지 마라. 바로 구현해라. task() 또는 서브에이전트를 사용하지 마라. planning 모드로 들어가지 마라."
```

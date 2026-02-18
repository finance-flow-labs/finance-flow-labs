---
name: macro-opencode-analysis
description: OpenCode 에이전트 실행(Codex xhigh)으로 finance-flow-labs의 매크로 분석 기능을 구현/개선한다. 퀀트 시그널, strategist/risk 분석문 생성, DB 저장, CLI 연결, 대시보드 노출을 다룰 때 사용한다. 애플리케이션 코드에 직접 OpenAI HTTP 호출을 넣지 않도록 강제해야 할 때 이 스킬을 사용한다.
---

# 매크로 OpenCode 분석

## 개요

`finance-flow-labs`의 매크로 분석 기능을 OpenCode 에이전트 워크플로로 구현한다.

분석 텍스트 생성은 OpenCode 실행 경로 또는 결정론적(fallback) 경로를 사용하고, 애플리케이션 코드에 직접 OpenAI HTTP 요청을 추가하지 않는다.

## 필수 규칙

- 구현 실행은 OpenCode를 사용한다.
- OpenCode 실행 모델은 Codex xhigh를 사용한다.
- 앱 코드에 OpenAI 직접 호출(`urllib`/`requests`로 OpenAI 엔드포인트 호출)을 추가하지 않는다.
- 기능 단위로 PR을 분리하고, 완료 시 PR URL을 공유한다.

## 빠른 시작

1. `references/finance-flow-labs-context.md`를 읽는다.
2. 프롬프트 품질이 흔들리면 `references/opencode-prompt-template.md`를 사용한다.
3. 기능 범위를 한 덩어리(단일 슬라이스)로 고정한다.
4. 검증을 실행한다(`PYTHONPATH=. pytest -q` + 필요한 스모크 테스트).
5. 커밋 후 PR을 연다.

## 구현 워크플로

### 1) 단일 기능 슬라이스로 범위를 고정한다

아래 중 정확히 하나를 선택한다.
- 퀀트 시그널 로직 수정
- strategist/risk 생성 경로 수정
- 저장 스키마/리포지토리 수정
- CLI 옵션/러너 수정
- 대시보드 섹션 수정

### 2) 레이어 경계를 지킨다

- `src/research/macro_analysis.py`: 퀀트 로직만 담당
- `src/research/agent_views.py`: 결정론적 합성/뷰 구성 담당
- `src/research/opencode_runner.py`: OpenCode 호출 + JSON 파싱/실패 처리 담당
- `src/research/flow_runner.py`: 오케스트레이션 + 저장 연결 담당
- `src/ingestion/cli.py`: 명령 인터페이스만 담당

### 3) OpenAI 직접 호출 금지를 검증한다

수정 전/후 아래를 확인한다.

```bash
grep -RIn "api.openai.com\|chat/completions\|responses" src
```

애플리케이션 플로우 파일에서 결과가 비어 있어야 한다.

### 4) 테스트로 검증한다

아래를 실행한다.

```bash
PYTHONPATH=. pytest -q
```

CLI 변경이 있으면 PR 설명에 스모크 실행 커맨드를 포함한다.

## PR 작성 기준

모든 기능 PR에는 아래를 포함한다.
- 무엇이 바뀌었는지(모듈 단위 요약)
- OpenCode 에이전트 아키텍처를 어떻게 유지했는지
- 테스트 결과(`PYTHONPATH=. pytest -q`)
- 마이그레이션/수동 작업 여부

## 참고 문서

- 저장소 구조/계약/명령 패턴: `references/finance-flow-labs-context.md`
- OpenCode 실행 프롬프트 템플릿: `references/opencode-prompt-template.md`

## 자주 하는 실수

- `cli.py`에 오케스트레이션 로직을 섞어 넣기
- 앱 코드에 직접 provider HTTP 클라이언트를 다시 추가하기
- 여러 기능 슬라이스를 하나의 PR에 묶기
- 러너 실패 시 fallback 경로 테스트를 생략하기

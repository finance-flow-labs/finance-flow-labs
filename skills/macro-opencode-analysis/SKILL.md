---
name: macro-opencode-analysis
description: finance-flow-labs에서 매크로 분석 파이프라인(quant 신호 계산, strategist/risk 관점 생성, 합성, DB 저장, CLI 실행)을 구현하거나 수정할 때 사용한다. 애플리케이션 코드에 직접 OpenAI HTTP 호출을 넣지 않고 OpenCode 실행 경로와 결정론적 fallback을 유지해야 하는 작업에 적용한다.
---

# 매크로 분석 구현

## 개요

이 스킬은 `finance-flow-labs`의 매크로 분석 기능을 일관된 구조로 구현하기 위한 작업 지침이다.

핵심 원칙은 아래 두 가지다.
- 분석 텍스트는 OpenCode 실행 경로를 사용해 생성한다.
- 앱 코드에는 직접 OpenAI HTTP 호출을 추가하지 않는다.

## 작업 범위

아래 중 **한 가지 기능 슬라이스**만 선택해 구현한다.
- 퀀트 시그널 계산 로직 수정
- strategist/risk 생성 경로 수정
- 합성(synthesis) 규칙 수정
- 저장소/스키마 연동 수정
- CLI 옵션/동작 수정
- 대시보드 노출 경로 수정

## 구현 워크플로

### 1) 범위 고정

한 PR에는 하나의 기능 슬라이스만 포함한다.

### 2) 레이어 경계 유지

- `src/research/macro_analysis.py`: 퀀트 로직
- `src/research/agent_views.py`: 결정론적 합성/뷰 구성
- `src/research/opencode_runner.py`: OpenCode 호출 및 응답 파싱
- `src/research/flow_runner.py`: 오케스트레이션 및 저장 연결
- `src/ingestion/cli.py`: 명령 인터페이스

### 3) 생성 경로 구현

- strategist/risk 텍스트는 OpenCode runner에서 생성한다.
- 실행 실패/파싱 실패 시 결정론적 fallback으로 안전하게 복구한다.

### 4) 저장 및 실행 연결

- 분석 결과를 repository 계층으로 저장한다.
- CLI 실행 시 엔진/모델 모드가 결과 요약에 드러나게 유지한다.

### 5) 테스트 보강

아래 테스트를 기능에 맞게 추가/수정한다.
- `tests/test_macro_analysis_pipeline.py`
- `tests/test_macro_analysis_cli.py`
- 필요 시 repository/smoke 테스트

## 필수 품질 기준

### 직접 OpenAI HTTP 호출 금지

수정 전/후 아래 명령으로 확인한다.

```bash
grep -RIn "api.openai.com\|chat/completions\|responses" src
```

매크로 분석 플로우 코드에서 결과가 비어 있어야 한다.

### fallback 보장

OpenCode 실행 실패 시에도 파이프라인은 결정론적 출력으로 완료되어야 하며, 해당 경로를 테스트로 보장한다.

## 검증 명령

```bash
PYTHONPATH=. pytest -q
```

CLI 변경이 있다면 PR 본문에 스모크 실행 커맨드를 함께 남긴다.

## PR 체크리스트

- 변경 파일/모듈 요약
- 아키텍처 준수 여부(직접 HTTP 호출 없음)
- 테스트 결과(`PYTHONPATH=. pytest -q`)
- 마이그레이션 또는 수동 작업 필요 여부
- PR URL 공유

## 참고 문서

- 저장소 구조/테이블/테스트 맵: `references/finance-flow-labs-context.md`
- 구현용 프롬프트 템플릿: `references/opencode-prompt-template.md`

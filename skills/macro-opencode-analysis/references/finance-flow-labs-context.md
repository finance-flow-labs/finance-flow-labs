# Finance Flow Labs 컨텍스트

## 핵심 파일

- `src/research/macro_analysis.py` - 퀀트 시그널 계산
- `src/research/agent_views.py` - 결정론적 합성용 뷰/페이로드 구성
- `src/research/opencode_runner.py` - OpenCode CLI 실행 및 응답 파싱
- `src/research/flow_runner.py` - quant → views → synthesis → persistence 오케스트레이션
- `src/ingestion/cli.py` - `run-macro-analysis` 명령 연결
- `src/ingestion/postgres_repository.py` - 저장소 읽기/쓰기

## 저장 테이블

- `macro_series_points`
  - 마이그레이션: `migrations/004_macro_series_points.sql`
- `macro_analysis_results`
  - 마이그레이션: `migrations/005_macro_analysis_results.sql`

## 확장 대상 테스트

- `tests/test_macro_analysis_pipeline.py`
- `tests/test_macro_analysis_cli.py`
- `tests/test_macro_analysis_repository.py`
- `tests/test_cli_smoke.py`

## 검증 명령

```bash
PYTHONPATH=. pytest -q
```

선택적 타깃 실행:

```bash
PYTHONPATH=. pytest -q tests/test_macro_analysis_pipeline.py
PYTHONPATH=. pytest -q tests/test_macro_analysis_cli.py
```

## 아키텍처 제약

- 앱 로직에 직접 provider HTTP 호출 코드를 넣지 않는다.
- 생성형 분석 텍스트 경계는 OpenCode runner로 유지한다.
- 결정론적 fallback 경로는 항상 동작하고 테스트로 보장한다.

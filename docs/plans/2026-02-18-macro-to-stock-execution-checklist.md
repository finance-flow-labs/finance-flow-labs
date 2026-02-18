# Macro-to-Stock Execution Checklist

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 데이터 수집 이후 단계(매크로 분석 -> 섹터 추천/분석 -> 주식 추천/분석)를 실제 실행 가능한 코드와 산출물로 완성한다.

**Architecture:** 기존 ingestion 결과(canonical data)를 입력으로 받아, 각 단계를 독립 모듈로 나눠 점진적으로 연결한다. 각 단계는 `입력 계약 -> 계산 로직 -> 저장 -> 조회/시각화`를 동일한 패턴으로 구현하고, 단계별 테스트와 E2E 테스트를 모두 통과해야 한다.

**Tech Stack:** Python, PostgreSQL(Supabase), SQL migrations, pytest, Streamlit

---

## 작업 규칙 (반드시 준수)

- 각 작업은 **한 번에 끝낼 수 있는 단위(60~120분)** 로 나눈다.
- 매 작업마다 `실패 테스트 -> 최소 구현 -> 통과 확인` 순서로 진행한다.
- 완료 기준은 아래 4개를 모두 만족해야 한다.
  1. 코드 구현
  2. 테스트 통과
  3. DB 산출물 저장(해당 시)
  4. 문서/런북 업데이트

---

### Task 1: 공통 출력 계약(스키마 + 타입) 고정

**Timebox:** 60~90분

**Files:**
- Create: `src/research/__init__.py`
- Create: `src/research/contracts.py`
- Create: `tests/test_research_contracts.py`

**Checklist:**
- [ ] `MacroRegime`, `SectorRecommendation`, `SectorAnalysis`, `StockRecommendation`, `StockDecisionPacket` 데이터 구조 정의
- [ ] 필수 필드(예: `as_of`, `score`, `confidence`, `rationale`) 명시
- [ ] 계약 테스트 작성(필수 필드 누락 시 실패)
- [ ] `pytest tests/test_research_contracts.py -q` 통과

**Definition of Done:**
- 모든 하위 모듈이 사용할 공통 계약이 코드/테스트로 고정됨

---

### Task 2: 매크로 분석 v1 (레짐 산출)

**Timebox:** 90~120분

**Files:**
- Create: `src/research/macro_analysis.py`
- Create: `tests/test_macro_analysis.py`

**Checklist:**
- [ ] 입력: canonical macro series(FRED/ECOS) 레코드 집합
- [ ] 출력: `regime`(예: expansion/slowdown), `confidence`, `rationale`
- [ ] 규칙 기반 최소 로직 구현(임계값 테이블)
- [ ] 경계값 테스트(상승/하락/중립) 작성
- [ ] `pytest tests/test_macro_analysis.py -q` 통과

**Definition of Done:**
- 같은 입력에 대해 항상 동일한 매크로 레짐 결과를 반환

---

### Task 3: 매크로 결과 저장 경로 추가

**Timebox:** 60~90분

**Files:**
- Create: `migrations/004_macro_regimes.sql`
- Modify: `src/ingestion/postgres_repository.py`
- Create: `tests/test_macro_regime_repository.py`

**Checklist:**
- [ ] `macro_regimes` 테이블 생성(`as_of`, `regime`, `confidence`, `rationale`, `lineage_id`)
- [ ] 저장/최근 조회 메서드 추가(`write_macro_regime`, `read_latest_macro_regime`)
- [ ] 저장/조회 테스트 작성
- [ ] `pytest tests/test_macro_regime_repository.py -q` 통과

**Definition of Done:**
- 매크로 분석 결과가 DB에 저장되고 최신 상태 조회 가능

---

### Task 4: 섹터 추천 엔진 v1

**Timebox:** 90~120분

**Files:**
- Create: `src/research/sector_recommendation.py`
- Create: `tests/test_sector_recommendation.py`

**Checklist:**
- [ ] 입력: 최신 macro regime + sector feature snapshot
- [ ] 출력: 섹터 Top-N(`sector`, `score`, `confidence`, `reason_codes`)
- [ ] 점수 계산식(가중합) 구현 및 동률 처리 규칙 정의
- [ ] 추천 결과 정렬/개수 제한 테스트 작성
- [ ] `pytest tests/test_sector_recommendation.py -q` 통과

**Definition of Done:**
- 섹터 추천이 재현 가능하게 산출되고 근거 코드(reason code) 포함

---

### Task 5: 섹터 분석 리포트 v1

**Timebox:** 60~90분

**Files:**
- Create: `src/research/sector_analysis.py`
- Create: `tests/test_sector_analysis.py`

**Checklist:**
- [ ] 입력: 추천 섹터 리스트 + 섹터별 기초 지표
- [ ] 출력: 섹터별 강점/약점/리스크 요약
- [ ] 리스크 플래그(변동성 과다, 데이터 부족) 규칙 추가
- [ ] 리포트 필드 누락 방지 테스트 작성
- [ ] `pytest tests/test_sector_analysis.py -q` 통과

**Definition of Done:**
- 추천 섹터 각각에 대해 최소 1개의 분석 리포트 산출

---

### Task 6: 주식 추천 엔진 v1

**Timebox:** 90~120분

**Files:**
- Create: `src/research/stock_recommendation.py`
- Create: `tests/test_stock_recommendation.py`

**Checklist:**
- [ ] 입력: 추천 섹터 + 종목 유니버스 + 필터(유동성/거래정지 등)
- [ ] 출력: 종목 Top-N(`ticker`, `score`, `rank`, `reject_reason`)
- [ ] 탈락 사유 기록 로직 구현
- [ ] 필터 및 랭킹 정확성 테스트 작성
- [ ] `pytest tests/test_stock_recommendation.py -q` 통과

**Definition of Done:**
- 추천/탈락 결과를 모두 재현 가능하게 추적할 수 있음

---

### Task 7: 주식 분석 의사결정 패킷 v1

**Timebox:** 60~90분

**Files:**
- Create: `src/research/stock_analysis.py`
- Create: `tests/test_stock_analysis.py`

**Checklist:**
- [ ] 입력: 추천 종목 + 재무/가격/이벤트 데이터
- [ ] 출력: `thesis`, `risk`, `trigger`, `uncertainty` 패킷 생성
- [ ] 필수 섹션 누락 시 실패 테스트 작성
- [ ] `pytest tests/test_stock_analysis.py -q` 통과

**Definition of Done:**
- 각 추천 종목마다 표준화된 투자 판단 패킷 제공

---

### Task 8: End-to-End Flow Runner 연결

**Timebox:** 90~120분

**Files:**
- Create: `src/research/flow_runner.py`
- Modify: `src/ingestion/cli.py`
- Create: `tests/test_flow_runner_e2e.py`

**Checklist:**
- [ ] 신규 CLI 명령 추가(예: `run-research-flow`)
- [ ] 실행 순서 고정: macro -> sector rec -> sector analysis -> stock rec -> stock analysis
- [ ] 중간 결과 실패 시 종료/로그 정책 구현
- [ ] E2E 테스트에서 단계별 산출물 존재 확인
- [ ] `pytest tests/test_flow_runner_e2e.py -q` 통과

**Definition of Done:**
- 단일 명령으로 전체 연구 흐름을 실행 가능

---

### Task 9: Streamlit 대시보드 확장

**Timebox:** 60~90분

**Files:**
- Modify: `src/dashboard/app.py`
- Create: `tests/test_dashboard_research_sections.py`

**Checklist:**
- [ ] 매크로 레짐 카드 섹션 추가
- [ ] 섹터 추천/분석 섹션 추가
- [ ] 주식 추천/분석 패킷 섹션 추가
- [ ] 빈 데이터 상태(Empty state) UI 처리
- [ ] `pytest tests/test_dashboard_research_sections.py -q` 통과

**Definition of Done:**
- 운영 대시보드에서 전체 흐름의 최신 결과를 시각적으로 확인 가능

---

### Task 10: 운영 문서/검증 마감

**Timebox:** 60~90분

**Files:**
- Modify: `docs/ingestion-runbook.md`
- Modify: `docs/FLOW_STATUS_MACRO_TO_STOCK_2026-02-18.md`

**Checklist:**
- [ ] 새 CLI 명령과 실행 예시 추가
- [ ] 장애 대응(실패 단계 식별/재시도 절차) 추가
- [ ] Stage 상태를 구현 결과 기준으로 업데이트
- [ ] 전체 테스트 1회 실행: `pytest -q`
- [ ] 운영 점검 체크 완료 여부 기록

**Definition of Done:**
- 코드/대시보드/운영 문서가 동일한 현재 상태를 반영

---

## 최종 완료 체크

- [ ] 모든 Task의 테스트가 통과했다.
- [ ] DB에 단계별 산출물이 저장된다.
- [ ] 대시보드에서 6단계 흐름 결과를 조회할 수 있다.
- [ ] 문서(`runbook`, `flow status`)가 최신 상태다.
- [ ] 회귀 테스트 후 PR 리뷰 준비 완료.

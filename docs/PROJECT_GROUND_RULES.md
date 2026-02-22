# finance-flow-labs Project Ground Rules (v0.1)

## 0) North Star
`거시경제 → 섹터 → 개별주`의 근거 기반 분석으로 **안정성과 수익률을 동시에 개선**하고,
예측/실행/결과를 DB에 축적해 **지속적으로 투자 노하우를 학습**하는 시스템을 만든다.

---

## 1) Product Scope (고정)
1. 미국 거시경제 분석
2. 섹터 분석
3. 개별주 분석
4. 모의투자(포트폴리오/시그널 실행) 및 성과 추적
5. 예상수익률 vs 실현수익률 차이(오차) 분석 및 원인 분류
6. 웹 시각화 대시보드
7. OpenClaw 스킬 기반 온디맨드 리서치/리포트

---

## 2) Evidence & Decision Rules

### 2.1 Evidence Tier
- **HARD**: DB에 저장된 시계열/공시/공식지표/체결기록
- **SOFT**: 뉴스/해석/내러티브

### 2.2 의사결정 원칙
- HARD 근거 없는 결론은 `투자 실행 불가`.
- 모든 결론은 근거 소스/시점/신뢰도를 함께 기록한다.
- 리포트는 `사실(HARD)`과 `해석(SOFT)`을 반드시 분리한다.

### 2.3 Reproducibility
- 동일 입력이면 동일 산출이 나오도록 파이프라인을 함수형으로 유지한다.
- 모든 분석 결과에는 생성 시각, 데이터 스냅샷 기준 시각(as_of), lineage를 저장한다.

---

## 3) Learning Loop Rules (핵심)

### 3.1 Forecast Record (사전 기록)
분석이 투자 액션으로 이어질 때 다음을 저장한다.
- thesis_id
- horizon (예: 1W/1M/3M)
- expected_return_range
- expected_volatility / expected_drawdown
- key drivers (macro/sector/stock)
- confidence

### 3.2 Realization Record (사후 평가)
호라이즌 도달 시 자동 평가 저장:
- realized_return
- realized_volatility
- max_drawdown
- hit/miss
- forecast_error (예측-실현 차)

### 3.3 Attribution / Error Taxonomy
오차는 최소 아래 분류로 저장:
- data_lag
- regime_shift
- valuation_miss
- macro_miss
- execution_slippage
- risk_control_failure
- unknown

### 3.4 Policy Update Rule
- 동일 실패 유형 누적 시 룰/모델을 업데이트하고 변경 이력을 남긴다.
- 룰 변경은 테스트 + 문서 업데이트 + PR 머지로만 반영한다.

---

## 4) Risk & Portfolio Control (임시 기본값)
> 사용자 확정 전까지의 기본 안전 가드레일

- 단일 아이디어 최대 비중: 20%
- 레버리지 ETF(TQQQ/SOXL/TMF 등) 합산 최대: 25%
- 최대 허용 낙폭(MDD) 경보선: -20%
- 경보선 도달 시: 위험자산 자동 축소/현금성 비중 확대 제안

---

## 5) Engineering Rules
- 10분 루프당 **작은 개선 1개** 원칙
- 항상 `main` 동기화 후 feature branch에서 작업
- 테스트 통과 없이는 머지 금지
- PR 본문에 `왜(Why) / 무엇(What) / 검증(Validation)` 필수
- 민감정보/키/개인정보 커밋 금지

---

## 6) Delivery Rules
- 사용자에게는 핵심만 간결하게 보고
- 내부 토큰/런타임/저수준 로그는 노출하지 않음
- 막히면 즉시 blocker와 다음 안전한 액션을 보고

---

## 7) 10-Minute Autopilot Backlog Priority
1. DB 스키마: forecast/realization/attribution 저장 구조
2. 거시→섹터→종목 신호 체인 데이터 모델
3. 모의투자 엔진 + 성과 측정 (벤치마크 대비)
4. 오차 분석 자동화 배치
5. 웹 대시보드(성과/오차/근거 drill-down)
6. OpenClaw skill 패키지(요청형 리포트)

---

## 8) Definition of Done (단위 개선)
- 코드/문서 변경이 목표에 직접 기여
- 테스트 또는 재현 가능한 검증 로그 존재
- main에 머지 완료
- 다음 액션이 backlog에 명확히 연결됨

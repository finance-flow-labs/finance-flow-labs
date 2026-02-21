---
name: macro-analysis
description: 거시경제 멀티에이전트 토론 분석. Bull, Bear, Policy, Critic 서브에이전트 병렬 실행 후 수렴 인사이트 제공.
---

## 거시경제 멀티에이전트 분석 실행 순서

사용자 쿼리를 분석하여 관련 데이터를 수집한 후, 4개 전문 에이전트가 병렬로 토론하고 수렴합니다.

---

### Step 1: 데이터 수집

쿼리와 관련된 데이터를 Bash로 수집하라. 아래는 기본 수집 명령어이며, 쿼리에 따라 적절히 선택하라.

```bash
# 뉴스 피드
python -m src.analysis.cli news global_macro --limit 5
python -m src.analysis.cli news us_economy --limit 3
python -m src.analysis.cli news korea_economy --limit 3

# 공식 기관 발표
python -m src.analysis.cli official fed_monetary --limit 3
python -m src.analysis.cli official fed_speeches --limit 3
python -m src.analysis.cli official us_treasury --limit 3

# 주요 시계열 (DB에 데이터가 있는 경우)
python -m src.analysis.cli series fred FEDFUNDS --limit 12
python -m src.analysis.cli series fred CPIAUCSL --limit 12
python -m src.analysis.cli series fred UNRATE --limit 12
python -m src.analysis.cli series ecos 722Y001 --limit 12

# 이상 탐지
python -m src.analysis.cli anomaly fred CPIAUCSL
python -m src.analysis.cli anomaly fred FEDFUNDS

# 박종훈의 지식한방 최근 영상 (항상 실행)
python -m src.analysis.cli channel @kpunch --days 30 --max-videos 5
```

YouTube URL이 제공된 경우 추가로 실행:
```bash
python -m src.analysis.cli youtube "<URL>"
```

---

### Step 2: Bull·Bear·Policy 서브에이전트 병렬 디스패치

**단일 메시지에서 동시에** Task tool로 아래 3개를 실행하라 (병렬 실행 필수):

- **macro-bull 에이전트**: Step 1에서 수집한 데이터 전체를 컨텍스트로 제공하고, "위 데이터를 성장·기회 관점으로 분석하라. 쿼리: [사용자 쿼리]"라고 지시하라.

- **macro-bear 에이전트**: Step 1에서 수집한 데이터 전체를 컨텍스트로 제공하고, "위 데이터를 리스크·하락 관점으로 분석하라. 쿼리: [사용자 쿼리]"라고 지시하라.

- **macro-policy 에이전트**: Step 1에서 수집한 데이터 전체를 컨텍스트로 제공하고, "위 데이터를 통화정책 관점으로 분석하라. 쿼리: [사용자 쿼리]"라고 지시하라.

---

### Step 3: Critic 에이전트 디스패치

Step 2의 Bull·Bear·Policy 분석 결과를 모두 받은 후, **macro-critic 에이전트**를 실행하라:

- Step 2 세 에이전트의 분석 결과 전체를 컨텍스트로 제공하고, "위 세 분석의 약점과 공통 맹점을 비판하라. 쿼리: [사용자 쿼리]"라고 지시하라.

---

### Step 4: 수렴 합성

네 에이전트의 결과를 아래 형식으로 통합하여 최종 인사이트를 작성하라:

---
## 📊 거시경제 멀티에이전트 분석

**분석 주제:** [사용자 쿼리]
**분석 일시:** [현재 날짜]

---

### 🐂 Bull 포지션
[Bull 에이전트 결과 전체]

---

### 🐻 Bear 포지션
[Bear 에이전트 결과 전체]

---

### 🏛️ Policy 포지션
[Policy 에이전트 결과 전체]

---

### ⚡ Critic 비판
[Critic 에이전트 결과 전체]

---

### ✅ 공통 동의 사항
- [Bull·Bear·Policy가 공통으로 동의하는 사실 또는 방향]
- ...

### 🔥 핵심 이견
- [Bull vs Bear, 또는 Policy vs 시장 간 핵심 견해 차이]
- ...

### 🎯 수렴 인사이트
[네 관점을 종합하되 Critic의 비판을 반영한 균형 잡힌 최종 결론.
Critic이 지적한 맹점을 명시적으로 인정하고,
투자·정책·리스크 관리 관점에서 실용적 함의를 제시하라.]

### 📁 데이터 출처
- FRED: [사용한 시리즈 목록]
- ECOS: [사용한 시리즈 목록]
- 뉴스 피드: [사용한 카테고리]
- 공식 발표: [사용한 기관]
- YouTube: [수집한 채널/영상 제목]

---

## 주의사항

- Step 2의 3개 에이전트는 **반드시 병렬로 실행**하라 (단일 메시지, 여러 Task tool 호출).
- Step 3의 Critic은 Step 2가 **완료된 후** 순차적으로 실행하라.
- 수집된 데이터가 없는 시리즈(DB 미연결 등)는 뉴스·공식발표로 대체하라.
- 각 에이전트 결과 마지막 줄의 POSITION 요약을 수렴 합성에 반드시 반영하라.

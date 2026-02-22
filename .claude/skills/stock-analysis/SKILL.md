---
name: stock-analysis
description: 개별 주식 멀티에이전트 토론 분석. Bull/Bear/Fundamental/Value/Growth/Risk 서브에이전트 병렬 실행 후 Critic 순차 실행, 수렴 인사이트 제공. 한국(DART) 및 미국(SEC EDGAR) 모두 지원.
---

## 개별 주식 멀티에이전트 분석 실행 순서

사용자 쿼리에서 종목을 식별하고 관련 데이터를 수집한 후, 6개 전문 에이전트가 병렬로 분석하고 Critic이 비판한 뒤 수렴합니다.

> **기본 동작**: 종목명/티커가 포함된 자유 텍스트 입력을 지원합니다. ("삼성전자 분석해줘", "Analyze Apple", "TSMC 어때?")
> **시장 자동 감지**: 한국어 종목명 또는 `.KS`/`.KQ` 티커 → DART(KR), 영문 티커 → SEC EDGAR(US)

---

### Step 1: 종목 식별 및 데이터 수집

쿼리에서 종목을 파악하고 아래 명령어로 데이터를 수집하라.

#### 1-1. 종목 식별 (한국: DART / 미국: SEC EDGAR)

```bash
# 한국 종목 검색 (회사명 또는 티커)
python3 -m src.analysis.cli stock dart "삼성전자"

# 미국 종목 검색 (회사명 또는 티커)
python3 -m src.analysis.cli stock edgar "Apple"
```

검색 결과에서 회사명, 티커, corp_code(KR) 또는 CIK(US)를 확인하라.

#### 1-2. 재무제표/밸류에이션 수집

```bash
# 한국: 최근 2개년 재무제표 (corp_code 또는 티커)
python3 -m src.analysis.cli stock dart "005930" --year 2024
python3 -m src.analysis.cli stock dart "005930" --year 2023

# 미국: XBRL company facts (티커 또는 CIK)
python3 -m src.analysis.cli stock edgar "AAPL"

# 미국(선택): 주가/멀티플/컨센서스(FMP)
# 필요 ENV: FMP_API_KEY
python3 -m src.analysis.cli stock fmp "AAPL" --limit 5
```

> FMP 호출이 401/403 또는 플랜 제한으로 실패해도 분석을 중단하지 말고,
> EDGAR + 뉴스 + 거시 데이터 기반으로 계속 진행하라. FMP 미수집 항목은 Needs Data에 명시하라.

#### 1-3. 주식 관련 뉴스 수집

```bash
# 한국 주식/기업 뉴스
python3 -m src.analysis.cli news kr_stock_news --limit 5
python3 -m src.analysis.cli news kr_corp_news --limit 5
python3 -m src.analysis.cli news korea_economy --limit 3

# 미국 주식/기업 뉴스
python3 -m src.analysis.cli news us_stock_news --limit 5
python3 -m src.analysis.cli news global_macro --limit 3
```

#### 1-4. 거시경제 컨텍스트 (DB에 있을 경우)

```bash
python3 - <<'PY'
import os, json
from src.ingestion.postgres_repository import PostgresRepository
dsn = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
if dsn:
    repo = PostgresRepository(dsn=dsn)
    latest = repo.read_latest_macro_analysis(limit=1)
    print(json.dumps(latest, ensure_ascii=False, default=str))
else:
    print("[]")
PY
```

#### 1-5. 주요 거시 지표 (항상 수집)

```bash
python3 -m src.analysis.cli series fred FEDFUNDS --limit 6
python3 -m src.analysis.cli series ecos 722Y001 --limit 6
```

---

### Step 2: Bull·Bear·Fundamental·Value·Growth·Risk 서브에이전트 병렬 디스패치

**단일 메시지에서 동시에** Task tool로 아래 6개를 실행하라 (병렬 실행 필수):

Step 1에서 수집한 전체 데이터(재무제표, 뉴스, 거시 컨텍스트)를 각 에이전트의 컨텍스트로 제공하라.

- **stock-bull 에이전트**: "위 데이터를 주가 상승 촉매·성장 동력 관점으로 분석하라. 종목: [종목명 (티커)], 시장: [KR/US]"
- **stock-bear 에이전트**: "위 데이터를 주가 하락 위험·실적 리스크 관점으로 분석하라. 종목: [종목명 (티커)], 시장: [KR/US]"
- **stock-fundamental 에이전트**: "위 재무제표를 심층 분석하라. 종목: [종목명 (티커)], 시장: [KR/US]"
- **stock-value 에이전트**: "위 데이터를 이용해 내재가치를 평가하라. 종목: [종목명 (티커)], 시장: [KR/US]"
- **stock-growth 에이전트**: "위 데이터를 성장 잠재력 관점으로 분석하라. 종목: [종목명 (티커)], 시장: [KR/US]"
- **stock-risk 에이전트**: "위 데이터에서 리스크 요인을 분석하라. 종목: [종목명 (티커)], 시장: [KR/US]"

---

### Step 3: Critic 에이전트 디스패치

Step 2의 6개 분석 결과를 모두 받은 후, **stock-critic 에이전트**를 순차 실행하라:

- 6개 에이전트의 분석 결과 전체를 컨텍스트로 제공하고,
  "위 6개 분석의 약점, 공통 맹점, 과장된 가정을 비판하라. 종목: [종목명 (티커)]"라고 지시하라.

---

### Step 4: 수렴 합성

7개 에이전트의 결과를 아래 형식으로 통합하여 최종 인사이트를 작성하라:

---
## 📈 개별 주식 멀티에이전트 분석

**종목:** [회사명] ([티커])
**시장:** [KR / US]
**분석 기준일:** [현재 날짜]

---

### 🐂 Bull 포지션
[Bull 에이전트 결과 전체]

---

### 🐻 Bear 포지션
[Bear 에이전트 결과 전체]

---

### 📊 Fundamental 포지션
[Fundamental 에이전트 결과 전체]

---

### 💎 Value 포지션
[Value 에이전트 결과 전체]

---

### 🚀 Growth 포지션
[Growth 에이전트 결과 전체]

---

### ⚠️ Risk 포지션
[Risk 에이전트 결과 전체]

---

### ⚡ Critic 비판
[Critic 에이전트 결과 전체]

---

### ✅ 공통 동의 사항
- [여러 에이전트가 공통으로 동의하는 사실 또는 방향]
- ...

### 🔥 핵심 이견
- [Bull vs Bear, Value vs Growth 등 핵심 견해 차이]
- ...

### 🎯 수렴 인사이트
[7개 관점을 종합하되 Critic의 비판을 반영한 균형 잡힌 최종 결론.
투자·리스크 관리 관점에서 실용적 함의를 제시하라.
매수/중립/매도 성향을 명시하되, 투자 권유가 아님을 고지하라.]

### 📁 데이터 출처
- 재무제표: [DART / SEC EDGAR]
- 뉴스: [사용한 피드 목록]
- 거시 컨텍스트: [macro_analysis_results 포함 여부]
- 거시 지표: [FRED, ECOS 사용 시리즈]

---

### Step 5: 분석 결과 DB 저장 (선택)

`SUPABASE_DB_URL` 또는 `DATABASE_URL`이 설정된 경우, Step 4 최종 결과를 `stock_analysis_results`에 저장하라.

저장 시 필드 매핑(핵심):
- `ticker`: 종목 티커 (예: "005930", "AAPL")
- `company_name`: 회사명
- `market`: "KR" 또는 "US"
- `bull_case`: Bull 포지션 원문
- `bear_case`: Bear 포지션 원문
- `fundamental_case`: Fundamental 포지션 원문
- `value_case`: Value 포지션 원문
- `growth_case`: Growth 포지션 원문
- `risk_case`: Risk 포지션 원문
- `critic_case`: Critic 비판 원문
- `narrative`: 수렴 인사이트 본문

예시 실행(필요 시):
```bash
python3 - <<'PY'
import os
from datetime import datetime, timezone
from uuid import uuid4
from src.ingestion.postgres_repository import PostgresRepository

dsn = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
if not dsn:
    raise SystemExit("DB DSN not set; skip persistence")

repo = PostgresRepository(dsn=dsn)
repo.write_stock_analysis_result(
    {
        "run_id": str(uuid4()),
        "ticker": "005930",
        "company_name": "삼성전자",
        "market": "KR",
        "as_of": datetime.now(timezone.utc).isoformat(),
        "bull_case": "...",
        "bear_case": "...",
        "fundamental_case": "...",
        "value_case": "...",
        "growth_case": "...",
        "risk_case": "...",
        "critic_case": "...",
        "narrative": "...",
        "model": "claude-sonnet-4-6",
    }
)
print("saved")
PY
```

DB가 없거나 저장 중 예외가 발생하면, 저장을 건너뛰고 Step 4 리포트 출력을 계속 진행하라.

---

## 주의사항

- Step 2의 6개 에이전트는 **반드시 병렬로 실행**하라 (단일 메시지, 여러 Task tool 호출).
- Step 3의 Critic은 Step 2가 **완료된 후** 순차적으로 실행하라.
- 재무제표 수집 실패(API 키 미설정 등)는 건너뛰고 뉴스·공시로 대체하라.
- `series`, `anomaly` 명령어가 오류를 반환하면 자동으로 건너뛰고 계속 진행하라.
- 각 에이전트 결과 마지막 줄의 POSITION 요약을 수렴 합성에 반드시 반영하라.
- 투자 결론은 항상 "이 분석은 투자 권유가 아닙니다" 고지를 포함하라.

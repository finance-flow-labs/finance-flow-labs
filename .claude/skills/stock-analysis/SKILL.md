---
name: stock-analysis
description: 개별 주식 멀티에이전트 토론 분석. Bull/Bear/Fundamental/Value/Growth/Risk 서브에이전트 병렬 실행 후 Critic 순차 실행, 수렴 인사이트 제공. 한국(DART) 및 미국(SEC EDGAR) 모두 지원하며 무료 공개 데이터(공시/IR/공공기관) 우선 수집 + FMP 스냅샷 상시 시도.
---

## 개별 주식 멀티에이전트 분석 실행 순서

사용자 쿼리에서 종목을 식별하고 관련 데이터를 수집한 후, 6개 전문 에이전트가 병렬로 분석하고 Critic이 비판한 뒤 수렴합니다.

> **기본 동작**: 종목명/티커가 포함된 자유 텍스트 입력을 지원합니다. ("삼성전자 분석해줘", "Analyze Apple", "TSMC 어때?")
> **시장 자동 감지**: 한국어 종목명 또는 `.KS`/`.KQ` 티커 → DART(KR), 영문 티커 → SEC EDGAR(US)
>
> **시간 정합성 규칙(매우 중요)**
> - 연도를 하드코딩하지 말고, **현재 시점 기준 최신 데이터**를 사용하라.
> - KR 분석에서 `Y-1` 연간(사업보고서) 데이터가 비어 있으면, 자동으로 `Y-2` 연간 + `Y-1/Y` 최신 분기/잠정 공시 신호로 보완하라.
> - 리포트 본문에 반드시 **"데이터 기준 시점"**과 **"fallback 이유"**를 명시하라.
>
> **현재가격 강제 규칙(필수)**
> - 분석 시작 전에 **반드시 현재가격(또는 최신 체결가)**를 수집하라.
> - 최소 필드: `price`, `as_of`(로컬/UTC 시각), `source`.
> - 가격 수집에 실패하면 매수/중립/매도 결론을 내리지 말고 `Needs Data`로 종료하라.
>
> **타이밍/과열 검증 규칙(필수)**
> - 현재가만 보지 말고, `1M/3M/6M/1Y 수익률`과 `52주 고점 대비 괴리`를 함께 계산하라.
> - 단기 급등(예: 3M 수익률 > +50% 또는 6M > +100%) + 52주 고점 근접(예: -3% 이내)인 경우,
>   밸류가 싸 보여도 기본 결론은 `추격매수 금지`/`조정 시 분할`로 보수화하라.
> - 리포트에 "좋은 종목"과 "좋은 가격"을 분리해 서술하라.

### 무료 공개 데이터 우선 + FMP 상시 시도 원칙 (필수)

- **항상 무료/공개 데이터부터 수집**하라: DART(한국), SEC EDGAR(미국), 회사 IR 페이지, 공공기관(CMS/FRED/ECOS).
- **FMP는 매번 반드시 호출 시도**하라(상시 시도). 성공 시 밸류/컨센서스 근거를 추가하라.
- FMP가 실패(키 미설정/401/403/플랜 제한)해도 분석을 중단하지 말고,
  무료 소스 기반으로 끝까지 수행한 뒤 FMP 미수집 항목만 `Needs Data`로 명시하라.
- 결과 본문과 데이터 출처 섹션에서 **무료 근거 vs FMP 보강 근거**를 구분하라.

---

### Step 1: 종목 식별 및 데이터 수집

쿼리에서 종목을 파악하고 아래 명령어로 데이터를 수집하라.

#### 1-1. 종목 식별 (한국: DART / 미국: SEC EDGAR)

```bash
# 한국 종목은 먼저 corp_code를 확정한다 (예: 삼성전자=00126380, stock_code=005930)
python3 - <<'PY'
import os, json, urllib.request, urllib.parse, zipfile, io, xml.etree.ElementTree as ET
api_key = os.getenv("OPEN_DART_API_KEY") or os.getenv("DART_API_KEY")
if not api_key:
    raise SystemExit("OPEN_DART_API_KEY (or DART_API_KEY) is required")
query = "삼성전자"
qs = urllib.parse.urlencode({"crtfc_key": api_key})
url = f"https://opendart.fss.or.kr/api/corpCode.xml?{qs}"
req = urllib.request.Request(url, headers={"User-Agent": "FinanceFlowLabs/1.0"})
with urllib.request.urlopen(req, timeout=40) as r:
    blob = r.read()
zf = zipfile.ZipFile(io.BytesIO(blob))
root = ET.fromstring(zf.read(zf.namelist()[0]))
matches = []
for li in root.findall("list"):
    corp_name = (li.findtext("corp_name") or "").strip()
    stock_code = (li.findtext("stock_code") or "").strip()
    if query in corp_name or query == stock_code:
        matches.append({
            "corp_code": (li.findtext("corp_code") or "").strip(),
            "corp_name": corp_name,
            "stock_code": stock_code,
            "modify_date": (li.findtext("modify_date") or "").strip(),
        })
print(json.dumps(matches[:10], ensure_ascii=False, indent=2))
PY

# 미국 종목 검색 (회사명 또는 티커)
python3 -m src.analysis.cli stock edgar "Apple"
```

검색 결과에서 회사명, 티커, **corp_code(KR)** 또는 CIK(US)를 확인하라.

#### 1-2. 재무제표/밸류에이션 수집 (무료 기본 + FMP 상시 시도)

```bash
# 한국: 최신 연차 우선 + fallback 연차 수집 (corp_code 필수, 연도 하드코딩 금지)
# 필요 ENV: OPEN_DART_API_KEY (무료 발급)
YEAR=$(date -u +%Y)
CORP_CODE="00126380"   # 예시: 삼성전자
python3 -m src.analysis.cli stock dart "$CORP_CODE" --year $((YEAR-1))
python3 -m src.analysis.cli stock dart "$CORP_CODE" --year $((YEAR-2))

# 한국: 최신 분기/잠정 공시 신호 보강 (Y-1/Y 기준)
python3 - <<'PY'
import json
from src.analysis.stock_client import DartStockClient
corp_code = "00126380"  # 대상 종목으로 교체
client = DartStockClient()
items = client.fetch_disclosures(corp_code, limit=20)
signals = [
    x for x in items
    if any(k in (x.get("report_nm", "")) for k in ["잠정", "분기보고서", "반기보고서", "사업보고서"])
]
print(json.dumps(signals, ensure_ascii=False, indent=2))
PY

# 미국(무료 기본): SEC EDGAR company facts + 최근 10-K/10-Q
python3 -m src.analysis.cli stock edgar "AAPL"

# 미국/한국(FMP 상시 시도): 주가/멀티플/컨센서스
# 필요 ENV: FMP_API_KEY (미설정이어도 호출 시도 후 실패 처리)
python3 -m src.analysis.cli stock fmp "AAPL" --limit 5
python3 -m src.analysis.cli stock fmp "005930.KS" --limit 5
```

**KR 최신성 fallback 규칙 (필수 적용):**
1. `Y-1` 연간 재무가 유효(핵심 계정: 매출/영업이익/당기순이익 존재)하면 이를 최신 연차로 사용.
2. `Y-1` 연간이 비거나 공백이면 `Y-2` 연간을 기준으로 사용하고, `Y-1/Y`의 분기·잠정 공시 신호로 최신성 보완.
3. DART 현금흐름 항목이 비어 있으면 숫자를 추정해 채우지 말고 `Needs Data`로 분리 표기.

> FMP는 **항상 호출 시도**하라.
> 단, 401/402/403, 플랜 제한, 키 미설정으로 실패해도 분석을 중단하지 말고
> **DART/EDGAR + 뉴스 + 거시 데이터(무료 소스)** 기반으로 계속 진행하라.
> FMP 미수집 항목은 `Needs Data`로 명시하고, 가능하면 EDGAR/DART 수치 기반 대체 추정(성장률, 마진 추세)을 제시하라.

#### 1-2b. 현재가격 수집 (필수 게이트)

```bash
# US 우선: FMP quote (성공 시 즉시 채택)
python3 -m src.analysis.cli stock fmp "AAPL" --limit 1

# US fallback 1: Yahoo Finance chart endpoint (키 불필요)
python3 - <<'PY'
import json, datetime, urllib.request
symbol = "AAPL"  # 티커 치환
url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=20) as r:
    payload = json.loads(r.read().decode("utf-8"))
result = payload["chart"]["result"][0]
meta = result.get("meta", {})
ts = (result.get("timestamp") or [None])[-1]
as_of = datetime.datetime.utcfromtimestamp(ts).isoformat() + "Z" if ts else None
print({
    "symbol": meta.get("symbol"),
    "price": meta.get("regularMarketPrice"),
    "currency": meta.get("currency"),
    "as_of": as_of,
    "source": "YAHOO_CHART_V8",
})
PY

# US fallback 2: stooq 공개 시세 (키 불필요, 지연 가능)
python3 - <<'PY'
import csv, io, urllib.request
symbol = "aapl.us"  # 티커 치환
url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=20) as r:
    row = list(csv.DictReader(io.StringIO(r.read().decode("utf-8"))))[0]
print(row)
PY

# KR 우선: FMP 005930.KS quote (플랜 제한 가능)
python3 -m src.analysis.cli stock fmp "005930.KS" --limit 1

# KR fallback(권장): 네이버 실시간 API (키 불필요)
python3 - <<'PY'
import json, urllib.request
code = "005930"  # 종목코드 치환
url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}|SERVICE_RECENT_ITEM:{code}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=20) as r:
    payload = json.loads(r.read().decode("euc-kr"))
item = payload["result"]["areas"][0]["datas"][0]
print({
    "code": item.get("cd"),
    "name": item.get("nm"),
    "price": item.get("nv"),
    "change": item.get("cv"),
    "change_pct": item.get("cr"),
    "market_state": item.get("ms"),
    "source": "NAVER_REALTIME",
})
PY

# KR fallback 2: Yahoo Finance chart endpoint (005930.KS)
python3 - <<'PY'
import json, datetime, urllib.request
symbol = "005930.KS"  # 티커 치환
url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=20) as r:
    payload = json.loads(r.read().decode("utf-8"))
result = payload["chart"]["result"][0]
meta = result.get("meta", {})
ts = (result.get("timestamp") or [None])[-1]
as_of = datetime.datetime.utcfromtimestamp(ts).isoformat() + "Z" if ts else None
print({
    "symbol": meta.get("symbol"),
    "price": meta.get("regularMarketPrice"),
    "currency": meta.get("currency"),
    "as_of": as_of,
    "source": "YAHOO_CHART_V8",
})
PY
```

> 가격 소스 우선순위(권장): **공식 거래소/브로커 API > FMP quote > Yahoo chart(v8) > 공개 시세 fallback(stooq/naver)**.
> fallback 가격을 쓴 경우 본문에 반드시 `fallback price`라고 명시하고 신뢰도를 한 단계 낮춰라.
> 가격이 끝내 확보되지 않으면 분석을 중단하고 `Needs Data: CURRENT_PRICE_UNAVAILABLE`를 반환하라.

#### 1-2c. 가격 위치/과열 체크 (필수)

```bash
# 1년 일봉 기준으로 1M/3M/6M/1Y 수익률 + 52주 고점 대비 괴리 계산 (Yahoo chart)
python3 - <<'PY'
import json, bisect, datetime, urllib.request
symbol = "000660.KS"  # 티커 치환
url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1y"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=20) as r:
    payload = json.loads(r.read().decode("utf-8"))
result = payload["chart"]["result"][0]
closes = result["indicators"]["quote"][0]["close"]
timestamps = result["timestamp"]
pairs = [(t, c) for t, c in zip(timestamps, closes) if c is not None]
all_t = [t for t, _ in pairs]
all_c = [c for _, c in pairs]
last_t, last_px = pairs[-1]

def ret(days: int):
    target = last_t - days * 86400
    i = bisect.bisect_left(all_t, target)
    if i >= len(all_c):
        i = len(all_c) - 1
    base = all_c[i]
    return (last_px / base - 1) * 100 if base else None

high_1y = max(all_c)
dist_to_high = (last_px / high_1y - 1) * 100 if high_1y else None
print({
    "symbol": symbol,
    "as_of": datetime.datetime.utcfromtimestamp(last_t).isoformat() + "Z",
    "ret_1m_pct": ret(30),
    "ret_3m_pct": ret(90),
    "ret_6m_pct": ret(180),
    "ret_1y_pct": ret(365),
    "dist_to_52w_high_pct": dist_to_high,
    "at_52w_high": abs(dist_to_high or 0) <= 0.5,
})
PY
```

> 과열 판정 예시: `ret_3m_pct > 50` 또는 `ret_6m_pct > 100`, 그리고 `dist_to_52w_high_pct >= -3`.
> 과열 시 기본 행동: `Buy` 대신 `Neutral to Buy-on-dip`, **추격매수 금지**, 분할 진입 비중 축소.

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

#### 1-6. 무료 검증 소스 보강 (권장)

아래는 키 없이 접근 가능한 검증 소스다. 업종에 맞는 것만 선택해 추가 수집하라.

```bash
# 회사 IR 페이지 (URL을 알고 있을 때)
python3 -m src.analysis.cli document "https://www.unitedhealthgroup.com/investors.html" --max-chars 4000

# 헬스케어 보험/정책 민감 종목일 때 CMS 공개 페이지
python3 -m src.analysis.cli document "https://www.cms.gov/medicare/payment/medicare-advantage-rates-statistics" --max-chars 4000
python3 -m src.analysis.cli document "https://www.cms.gov/medicare/health-drug-plans/part-c-d-performance-data" --max-chars 4000
```

> 특정 회사/섹터에서 공식기관 공개 데이터가 있으면 우선 채택하라.
> 단, 문서 수집이 실패해도 전체 분석은 계속 진행하라.

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
**현재가 기준:** [price] ([source], [as_of])
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

### 🧭 가격 위치/타이밍 점검
- [1M/3M/6M/1Y 수익률]
- [52주 고점 대비 괴리]
- [과열 여부 판정 + 추격매수/조정매수 가이드]

### 🎯 수렴 인사이트
[7개 관점을 종합하되 Critic의 비판을 반영한 균형 잡힌 최종 결론.
투자·리스크 관리 관점에서 실용적 함의를 제시하라.
매수/중립/매도 성향을 명시하되, 투자 권유가 아님을 고지하라.]

### 🧾 최종 의사결정 요약 (필수)
- `RECOMMENDATION:` [Buy / Neutral / Sell / Neutral to Buy-on-dip]
- `CONFIDENCE:` [0~1]
- `WHY NOW:` [핵심 2~3줄]
- `INVALIDATION TRIGGERS:` [3개 이내]
- `POSITION SIZING IDEA:` [분할/비중/리스크 캡]

### 📁 데이터 출처
- 무료 공개(필수): [DART / SEC EDGAR / IR / CMS 등 실제 사용 항목]
- 현재가 소스(필수): [예: KRX/NAVER realtime, FMP quote, Yahoo chart(v8), stooq + as_of]
- 가격 위치/타이밍 소스(필수): [Yahoo 1y chart 등 1M/3M/6M/1Y, 52주 고점 괴리 계산 근거]
- FMP(상시 시도): [성공 시 사용 근거, 실패 시 Needs Data와 실패 사유]
- 뉴스: [사용한 피드 목록]
- 거시 컨텍스트: [macro_analysis_results 포함 여부]
- 거시 지표: [FRED, ECOS 사용 시리즈]
- 데이터 시점/결손: [예: `Y-1` 연차 부재로 `Y-2` 연차 + `Y-1/Y` 공시 신호 사용, FMP 402 항목은 Needs Data 처리]

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
- 무료 공개 데이터(공시/IR/공공기관) 수집을 먼저 완료하고, FMP를 **항상 호출 시도**하라.
- FMP 실패(API 키 미설정/401/402/403/플랜 제한)는 분석 중단 사유가 아니다. 무료 근거로 계속 진행하라.
- 재무제표 수집 실패(API 키 미설정 등)는 건너뛰고 뉴스·공시로 대체하라.
- KR 분석에서 연도 하드코딩(예: 항상 2024) 금지. 항상 현재 시점 기준 `Y-1 → Y-2` fallback 규칙을 적용하라.
- **현재가격 수집은 필수 게이트**: 가격/시각/소스를 확보하기 전에는 결론을 내리지 말고, 실패 시 `Needs Data: CURRENT_PRICE_UNAVAILABLE`로 종료하라.
- **타이밍/과열 체크는 필수 게이트**: 1M/3M/6M/1Y 수익률과 52주 고점 괴리를 계산하고, 과열 시 기본 결론을 보수화(`Neutral to Buy-on-dip`)하라.
- **추격매수 금지 원칙**: 단기 급등 + 고점 근접 구간에서는 신규 비중을 축소하고, 조정/확인 후 분할 진입을 우선하라.
- `series`, `anomaly` 명령어가 오류를 반환하면 자동으로 건너뛰고 계속 진행하라.
- 각 에이전트 결과 마지막 줄의 POSITION 요약을 수렴 합성에 반드시 반영하라.
- 투자 결론은 항상 "이 분석은 투자 권유가 아닙니다" 고지를 포함하라.

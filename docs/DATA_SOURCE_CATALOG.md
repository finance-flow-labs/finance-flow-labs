# KR+US 금융 데이터 소스 카탈로그

**작성일**: 2026-02-18  
**목적**: 데이터베이스 구축을 위한 고신뢰도 외부 데이터 소스 맵

---

## 📊 데이터 레이어 분류 기준

- **GOLD**: 공식 정부/거래소 API, 무료 또는 합리적 비용, 법적 제약 최소
- **SILVER**: 상용 API, 검증된 품질, 명확한 재배포 조건
- **BRONZE**: 비공식 스크래핑/래퍼, 법적 불확실성, 안정성 보장 없음

---

## 🇺🇸 미국 데이터 소스

### GOLD Tier

#### 1. FRED (Federal Reserve Economic Data)
- **제공 기관**: Federal Reserve Bank of St. Louis
- **공식 URL**: https://fred.stlouisfed.org/docs/api/fred/
- **데이터 범위**: 
  - 매크로 경제 지표 (GDP, CPI, PPI, 실업률 등)
  - 금리, 통화량, 신용 데이터
  - 80만+ 시계열, 100+ 데이터 소스
- **업데이트 주기**: 일별~월별 (지표별 상이)
- **인증/제한**: 
  - API 키 필수 (무료 등록)
  - 무제한 호출 (공식 제한 없음, 합리적 사용 권장)
- **데이터 형식**: JSON, XML
- **법적 제약**: 퍼블릭 도메인 (Public Domain)
- **상용 이용**: ✅ 허용
- **재배포**: ✅ 허용 (출처 표기 권장)
- **Best Use**: 매크로 경제 분석, 금리 데이터, 시계열 연구

#### 2. ALFRED (Archival FRED)
- **제공 기관**: Federal Reserve Bank of St. Louis
- **공식 URL**: https://alfred.stlouisfed.org
- **데이터 범위**: FRED 데이터의 과거 개정본(vintages)
- **업데이트 주기**: FRED와 동일
- **인증/제한**: FRED API 동일
- **법적 제약**: FRED와 동일
- **Best Use**: 실시간 데이터 분석, 정책 평가 연구

#### 3. BEA (Bureau of Economic Analysis)
- **제공 기관**: U.S. Department of Commerce
- **공식 URL**: https://apps.bea.gov/API/signup/
- **데이터 범위**:
  - GDP 상세 구성 요소
  - 국제수지, 무역 통계
  - 산업별 GDP, 지역 경제 데이터
- **업데이트 주기**: 분기별~연별
- **인증/제한**:
  - API 키 필수 (무료 등록)
  - 100 calls/minute (등록 사용자)
- **데이터 형식**: JSON, XML
- **법적 제약**: 퍼블릭 도메인
- **상용 이용**: ✅ 허용
- **Best Use**: GDP 분석, 국제 무역, 지역 경제

#### 4. BLS (Bureau of Labor Statistics)
- **제공 기관**: U.S. Department of Labor
- **공식 URL**: https://www.bls.gov/bls/api_features.htm
- **데이터 범위**:
  - CPI, PPI (물가 지수)
  - 고용 통계 (실업률, 임금, 산업별 고용)
  - 생산성 지표
- **업데이트 주기**: 월별~연별
- **인증/제한**:
  - V1: 등록 불필요, 25 requests/day, 10 years data
  - V2: 등록 필요, 500 requests/day, 20 years data
- **데이터 형식**: JSON, Excel
- **법적 제약**: 퍼블릭 도메인
- **상용 이용**: ✅ 허용
- **Best Use**: 인플레이션 분석, 노동 시장 연구

#### 5. SEC EDGAR (공식 API)
- **제공 기관**: U.S. Securities and Exchange Commission
- **공식 URL**: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- **데이터 범위**:
  - 기업 공시 (10-K, 10-Q, 8-K, proxy 등)
  - XBRL 재무제표 데이터
  - 내부자 거래, 13F 기관 보유
  - Company submissions (data.sec.gov/submissions/)
- **업데이트 주기**: 실시간 (공시 제출 즉시)
- **인증/제한**:
  - API 키 불필요
  - 10 requests/second (User-Agent 필수)
  - Fair Access Rule 준수 필수
- **데이터 형식**: JSON, XML, HTML
- **법적 제약**: 퍼블릭 도메인
- **상용 이용**: ✅ 허용 (rate limit 준수)
- **재배포**: ✅ 허용
- **Best Use**: 기업 펀더멘털, 공시 분석, 규제 데이터
- **주의사항**: bulk download는 별도 규정 (https://www.sec.gov/developer)

---

### SILVER Tier

#### 6. Financial Modeling Prep (FMP)
- **공식 URL**: https://site.financialmodelingprep.com/developer/docs
- **데이터 범위**:
  - 실시간 주가 (미국 + 글로벌 40,000+ 종목)
  - 재무제표 (분기/연간, 30년 히스토리)
  - 애널리스트 추정치, 가격 목표
  - Earnings call transcripts
  - 내부자 거래, 13F filings
  - 경제 지표, Forex, Crypto, Commodities
- **업데이트 주기**: 실시간~일별
- **인증/제한**:
  - API 키 필수
  - Free: 250 calls/day
  - Starter ($14/mo): 300 calls/min
  - Professional ($99/mo): 750 calls/min, 30년 히스토리
- **데이터 형식**: JSON, CSV
- **법적 제약**:
  - **상용 이용**: 플랜별 상이 (Commercial 플랜 필요)
  - **재배포**: ❌ 금지 (자체 앱 내 사용만 허용)
- **Best Use**: 애플리케이션 개발, 알고리즘 트레이딩, 재무 분석
- **강점**: 광범위한 데이터 커버리지, 합리적 가격, 안정적 uptime

#### 7. Polygon.io (Massive)
- **공식 URL**: https://polygon.io
- **데이터 범위**:
  - 실시간 주가 (미국 전체 거래소, 32,000+ 종목)
  - Options (170만+ 계약)
  - Forex (1,750+ 페어)
  - Crypto, Futures
  - Tick-level 데이터, Level 2 quotes
- **업데이트 주기**: 실시간 (WebSocket), 분/일 aggregates
- **인증/제한**:
  - Free: 5 calls/min, EOD data only
  - Starter ($29/mo): unlimited calls, 15분 지연
  - Developer ($79/mo): unlimited, 15분 지연, 10년 히스토리
  - Advanced ($199/mo): 실시간, 20년+ 히스토리
  - Business ($1,999/mo): 기관용, SLA
- **데이터 형식**: JSON, CSV, WebSocket
- **법적 제약**:
  - **상용 이용**: Non-pro 플랜은 개인용만, Business 이상 필요
  - **재배포**: ❌ 금지 (거래소 규정)
- **Best Use**: 고빈도 트레이딩, 틱 데이터 분석, WebSocket 스트리밍
- **강점**: 낮은 레이턴시, 직접 거래소 연결, 99.9% uptime

#### 8. Alpha Vantage
- **공식 URL**: https://www.alphavantage.co
- **데이터 범위**:
  - 주가 (200,000+ 글로벌 티커, 20+ 거래소)
  - 50+ 기술 지표
  - 재무제표, 경제 지표
  - Forex, Crypto, Commodities
- **업데이트 주기**: 실시간~일별
- **인증/제한**:
  - Free: 25 requests/day, 500 calls/month
  - Premium ($49/mo): 75 calls/min, intraday data
  - Enterprise: 커스텀
- **데이터 형식**: JSON, CSV
- **법적 제약**:
  - **상용 이용**: Premium 이상 필요
  - **재배포**: 제한적 (약관 검토 필수)
- **Best Use**: 기술적 분석, 글로벌 시장 데이터
- **약점**: Free tier 제한 매우 엄격 (25 req/day)

#### 9. Nasdaq Data Link (구 Quandl)
- **공식 URL**: https://data.nasdaq.com
- **데이터 범위**:
  - 2천만+ 데이터셋 (금융, 경제, 대체 데이터)
  - NASDAQ, NYSE 주가
  - 경제 지표, 산업 데이터
  - Premium: 1분봉 intraday (NASDAQ 100 등)
- **업데이트 주기**: 데이터셋별 상이
- **인증/제한**:
  - Free: 50 calls/day (일부 데이터셋)
  - Premium: 데이터셋별 가격 상이
- **데이터 형식**: JSON, CSV, XML
- **법적 제약**: 데이터셋별 라이선스 상이 (확인 필수)
- **Best Use**: 대체 데이터, 특정 산업 데이터
- **주의사항**: 많은 무료 데이터셋이 중단됨 (WIKI EOD 등)

---

### BRONZE Tier (비공식/스크래핑)

#### 10. yfinance (Yahoo Finance 비공식 라이브러리)
- **GitHub**: https://github.com/ranaroussi/yfinance
- **공식 문서**: https://yfinance-python.org
- **데이터 범위**:
  - 글로벌 주가 (일봉, 1분~1개월봉)
  - 재무제표 (제한적)
  - 옵션 체인, 배당/분할
  - ETF/뮤추얼펀드 정보
- **업데이트 주기**: 실시간~15분 지연 (시장별 상이)
- **인증/제한**:
  - 인증 불필요
  - rate limit 없음 (과도 사용 시 IP 차단 가능)
- **데이터 형식**: Pandas DataFrame, CSV
- **법적 제약**:
  - ⚠️ **비공식 API**: Yahoo 공식 지원 없음
  - ⚠️ **상용 이용**: Yahoo 약관상 개인용만 허용
  - ⚠️ **재배포**: 법적 불확실성
  - ⚠️ **안정성**: API 변경 시 예고 없이 중단 가능
- **Best Use**: 프로토타이핑, 개인 연구, 백테스팅
- **주의사항**: 
  - 상업적 프로덕션 사용 부적합
  - 데이터 정확도 보장 없음
  - 법적 리스크 존재

#### 11. IEX Cloud 대안 (서비스 종료 2024.08.31)
- **상태**: ❌ 서비스 종료됨
- **대안**:
  - Databento (https://databento.com) - 기관용, 60+ 거래소
  - FMP, Polygon.io (위 참조)

---

## 🇰🇷 한국 데이터 소스

### GOLD Tier

#### 12. DART (전자공시시스템)
- **제공 기관**: 금융감독원
- **공식 URL**: https://opendart.fss.or.kr
- **개발자 가이드**: https://opendart.fss.or.kr/guide/main.do
- **데이터 범위**:
  - 공시보고서 원문 (XML)
  - 사업보고서 주요 정보
  - 재무제표 (상장법인, 분기별)
  - 지분공시 종합 정보
  - 주요사항보고서, 증권신고서
- **업데이트 주기**: 실시간 (공시 제출 즉시)
- **인증/제한**:
  - API 키 필수 (무료 등록)
  - 10,000 calls/day
  - 1 call/second 권장
- **데이터 형식**: JSON, XML
- **법적 제약**:
  - **상용 이용**: ✅ 허용 (출처 표기)
  - **재배포**: ✅ 허용 (가공 데이터 포함)
- **Best Use**: 한국 기업 펀더멘털, 재무제표 분석, 공시 모니터링
- **주의사항**: 
  - XBRL 재무제표는 별도 파싱 필요
  - 일부 데이터는 대용량 ZIP 제공

#### 13. ECOS (한국은행 경제통계시스템)
- **제공 기관**: 한국은행
- **공식 URL**: https://ecos.bok.or.kr/api/
- **데이터 범위**:
  - 통화/금융 통계 (기준금리, 통화량, 금리)
  - 물가 지수 (CPI, PPI)
  - 국민계정 (GDP, GNI)
  - 국제수지, 외환 보유액
  - 기업경영분석 (재무비율 통계)
- **업데이트 주기**: 일별~분기별 (지표별 상이)
- **인증/제한**:
  - API 키 필수 (무료 등록)
  - 10,000 calls/day (추정)
- **데이터 형식**: JSON, XML
- **법적 제약**:
  - **상용 이용**: ✅ 허용 (출처 표기)
  - **재배포**: ✅ 허용
- **Best Use**: 한국 매크로 경제 분석, 금리 데이터
- **참고**: Python 래퍼 https://github.com/seokhoonj/ecos

#### 14. KOSIS (국가통계포털)
- **제공 기관**: 통계청
- **공식 URL**: https://kosis.kr/openapi/
- **데이터 범위**:
  - 인구, 가구, 고용 통계
  - 산업/경제 활동 통계
  - 280,000+ 통계표
  - 1,500+ 조사 통계
- **업데이트 주기**: 월별~연별 (통계별 상이)
- **인증/제한**:
  - API 키 필수 (무료 등록)
  - 분당 호출 제한 있음 (정확한 수치 미공개, 2026년 변경 예정)
  - ⚠️ HTTP 프로토콜 종료 예정 (HTTPS만 지원)
- **데이터 형식**: JSON, XML
- **법적 제약**: 오픈 라이선스 (출처 표기)
- **Best Use**: 인구 통계, 산업 분류별 경제 데이터

#### 15. KRX 정보데이터시스템
- **제공 기관**: 한국거래소
- **공식 URL**: https://data.krx.co.kr
- **데이터 범위**:
  - 종목별 시세, 거래량
  - 투자자별 매매 동향
  - 지수 데이터
  - 공매도 현황
  - 상장 종목 정보
- **업데이트 주기**: 일별 (장 마감 후)
- **인증/제한**:
  - ⚠️ **공식 Open API 없음** (2026년 2월 기준)
  - 웹 인터페이스 통한 CSV/Excel 다운로드만 제공
  - Data Feed 서비스는 유료 라이선스 필요 (기관용)
- **법적 제약**:
  - **상용 이용**: 유료 계약 필요
  - **스크래핑**: ❌ 약관상 금지
- **Best Use**: EOD 시세 데이터 (수동 다운로드)
- **상용 대안**:
  - KOSCOM MDCS (https://data.koscom.co.kr) - 유료
  - ICE Data Services - KRX 피드 제공 (기관용)
  - Twelve Data (https://twelvedata.com/exchanges/XKRX) - 글로벌 서비스

---

### SILVER Tier

#### 16. FinanceDataReader (한국 중심 비공식 래퍼)
- **GitHub**: https://github.com/FinanceData/FinanceDataReader
- **데이터 범위**:
  - KRX 주식 (KOSPI, KOSDAQ, KONEX)
  - 미국 주식 (일부)
  - 환율, 암호화폐
  - **백엔드**: KRX 웹사이트, Naver Finance, Yahoo Finance 등
- **법적 제약**:
  - ⚠️ **비공식 스크래핑**: KRX 공식 API 아님
  - ⚠️ **상용 이용**: 법적 불확실성
  - ⚠️ **안정성**: 웹사이트 구조 변경 시 중단 가능
- **Best Use**: 개인 연구, 프로토타이핑
- **주의사항**: 프로덕션 환경 부적합

---

## 📋 데이터 레이어별 활용 전략

### GOLD → 데이터베이스 Primary Source
**권장 구성**:
```yaml
US_Macro:
  - FRED/ALFRED (경제 지표)
  - BEA (GDP, 무역)
  - BLS (고용, 물가)

US_Fundamentals:
  - SEC EDGAR (공시, 재무제표)

KR_Macro:
  - ECOS (경제 지표)
  - KOSIS (인구/산업 통계)

KR_Fundamentals:
  - DART (공시, 재무제표)
```

**장점**: 
- 법적 안전성 ✅
- 장기 안정성 ✅
- 재배포 가능 ✅
- 무료 또는 합리적 비용

**단점**:
- 시장 가격 데이터 제한적 (EDGAR는 가격 없음, DART도 마찬가지)
- 실시간 데이터 부족

---

### SILVER → 가격/시장 데이터 보완
**권장 구성**:
```yaml
US_Market_Data:
  - FMP (주가, 재무, 추정치) - $99/mo
  - Polygon.io (실시간, 틱 데이터) - $199/mo

KR_Market_Data:
  - KRX 수동 다운로드 (무료, EOD)
  - 또는 KOSCOM MDCS (유료 계약)
```

**장점**:
- 고품질 시장 데이터
- 안정적 인프라
- 명확한 상용 라이선스

**단점**:
- 재배포 제한 (자체 앱 내만 사용)
- 월 구독 비용

**비용 최적화**:
- 초기: FMP Starter ($14/mo) + DART/ECOS (무료)
- 스케일업: FMP Professional + Polygon Advanced

---

### BRONZE → 절대 피해야 할 경우
❌ **상용 서비스 백엔드로 사용 금지**:
- yfinance, FinanceDataReader 등
- 법적 리스크, 안정성 문제

✅ **허용 가능한 경우**:
- 내부 연구/백테스팅
- 프로토타입 검증
- 교육 목적

---

## ⚖️ 법적/상용 체크리스트

### 데이터베이스 구축 시 필수 확인사항

| 확인 항목 | GOLD | SILVER | BRONZE |
|---------|------|--------|--------|
| **상용 이용 명시 허용** | ✅ | 플랜별 | ❌ |
| **재배포 허용** | ✅ | ❌ | ❌ |
| **API 안정성 보장** | ✅ | ✅ | ❌ |
| **법적 리스크** | 없음 | 낮음 | 높음 |
| **SLA 제공** | 일부 | 유료 플랜 | 없음 |

### 권장 라이선스 전략
1. **GOLD 데이터는 DB에 적재 후 서비스 제공 가능**
   - FRED, BEA, BLS, DART, ECOS → ✅ 재배포 OK
   
2. **SILVER 데이터는 실시간 프록시 방식 권장**
   - FMP, Polygon → API 호출 결과를 즉시 전달
   - DB 캐싱은 단기 (1일 이내) 권장
   
3. **BRONZE 데이터는 내부 용도만**
   - 외부 서비스 노출 금지

---

## 🎯 실전 데이터 파이프라인 예시

### 최소 구성 (무료)
```python
# GOLD Tier만 사용
sources = {
    'us_macro': ['FRED', 'BEA', 'BLS'],
    'us_filings': ['SEC_EDGAR'],
    'kr_macro': ['ECOS', 'KOSIS'],
    'kr_filings': ['DART'],
    'kr_market': ['KRX_manual_download']  # EOD만
}

# 장점: 완전 무료, 법적 안전
# 단점: 실시간 가격 없음, KRX는 수동
```

### 권장 구성 (월 $100 내외)
```python
sources = {
    'us_macro': ['FRED', 'BEA', 'BLS'],
    'us_filings': ['SEC_EDGAR'],
    'us_market': ['FMP'],  # $99/mo
    'kr_macro': ['ECOS', 'KOSIS'],
    'kr_filings': ['DART'],
    'kr_market': ['FMP'],  # 한국 종목도 일부 커버
}

# 장점: 실시간 가격, 글로벌 커버리지
# 단점: KRX 데이터는 FMP가 완벽하지 않을 수 있음 (확인 필요)
```

### 프로덕션 구성 (월 $300+)
```python
sources = {
    'us_macro': ['FRED', 'BEA', 'BLS'],
    'us_filings': ['SEC_EDGAR'],
    'us_market': ['Polygon.io'],  # $199/mo, 실시간
    'us_fundamentals': ['FMP'],    # $99/mo, 재무제표
    'kr_macro': ['ECOS', 'KOSIS'],
    'kr_filings': ['DART'],
    'kr_market': ['KOSCOM_MDCS'],  # 유료 계약 (가격 문의 필요)
}

# 장점: 기관급 품질, SLA
# 단점: 비용
```

---

## 📌 중요 업데이트 (2026년 2월 기준)

1. **IEX Cloud 종료** (2024.08.31)
   - 대안: Databento, FMP, Polygon.io

2. **KOSIS HTTP 프로토콜 종료 예정**
   - HTTPS만 지원 (마이그레이션 필요)

3. **SEC EDGAR API 개선**
   - data.sec.gov/submissions/ 엔드포인트 추가
   - Company Facts API 안정화

4. **yfinance 법적 불확실성 증가**
   - Yahoo Finance 비공식 API 사용
   - 상업적 사용 명시 금지 (Yahoo 약관)

---

## ✅ 최종 권고사항

### "DB에 더 많은 정보를 수집할 수 있는가?"

**답변: YES, 단 계층별로 구분 필수**

#### 즉시 수집 가능 (법적 안전)
- ✅ FRED/ALFRED - 80만 시계열
- ✅ BEA - GDP, 무역 상세 데이터
- ✅ BLS - 고용, 물가 상세 데이터
- ✅ SEC EDGAR - 모든 미국 상장사 공시
- ✅ DART - 모든 한국 공시법인 데이터
- ✅ ECOS - 한국은행 전체 통계
- ✅ KOSIS - 28만 통계표

#### 유료 구독 후 수집 (재배포 제한)
- 💰 FMP - 주가, 재무제표 (자체 앱 내 사용만)
- 💰 Polygon.io - 실시간 시세 (자체 앱 내 사용만)

#### 수집 금지 (법적 리스크)
- ❌ yfinance 상업적 DB 적재
- ❌ KRX 웹사이트 자동 스크래핑
- ❌ FinanceDataReader 프로덕션 사용

---

## 📚 추가 참고 자료

- **SEC Fair Access**: https://www.sec.gov/os/webmaster-faq#code-support
- **DART API 개발가이드**: https://opendart.fss.or.kr/guide/main.do
- **FRED API 문서**: https://fred.stlouisfed.org/docs/api/fred/
- **BLS API 문서**: https://www.bls.gov/developers/api_signature_v2.htm

---

**면책 조항**: 본 문서는 2026년 2월 18일 기준 공개 정보를 바탕으로 작성되었습니다. 
실제 사용 전 각 데이터 제공자의 최신 약관 및 라이선스를 반드시 확인하시기 바랍니다.

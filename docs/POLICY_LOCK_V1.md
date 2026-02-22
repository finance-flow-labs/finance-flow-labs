# Policy Lock v1.1 (2026-02-22)

사용자 합의 기반 운영 정책(autopilot 기준).

## Confirmed by user
1. 투자 우주: **미국 + 한국 + 암호화폐**
2. 암호화폐 범위: **BTC/ETH + 상위 알트 일부 허용 (B)**
3. 최대 허용 MDD: **-30% (C)**
4. 리밸런싱 주기: **분기 (Quarterly)**
5. 보고 포맷: **상세형**
6. 한국 자산 범위: **지수 + ETF + 개별주 모두**
7. 집행 정책: **모의투자 자동, 실매매는 수동 승인(A)** + 추후 자동실행 옵션(C)
8. 보고 정책: **하루 1회 요약(B)** + **중요 이벤트 즉시(C)**

## Auto-selected defaults (assistant-owned; can be overridden)
- 레버리지 자산(TQQQ/SOXL/TMF 등) 합산 상한: **20%**
- 기본 비교 벤치마크(복합):
  - **45% QQQ**
  - **25% KOSPI200 proxy**
  - **20% BTC-USD**
  - **10% SGOV**
- 기본 평가 호라이즌: **1개월(Primary)**
  - 보조 모니터링: 1주(리스크 조기경보), 3개월(테제 검증)

## Crypto sleeve control
- BTC/ETH 합계가 crypto sleeve의 **최소 70%**
- 상위 알트 합계는 crypto sleeve의 **최대 30%**

## Reporting SLA
- Daily report: 한국시간 기준 1회 (상세형)
- Event alert: MDD 경보선 접근, 레짐 급변, 신호 무효화 시 즉시

## Open items
- 없음 (현재 정책 잠금 완료)

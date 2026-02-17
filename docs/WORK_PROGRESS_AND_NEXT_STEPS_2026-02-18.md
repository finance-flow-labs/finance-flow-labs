# Finance Flow Labs 진행 현황 및 다음 작업 (2026-02-18)

## 1) 지금까지 완료된 작업

- KR+US 데이터 수집 파이프라인 기본 골격 구현
  - raw/canonical/quarantine 저장 구조
  - ingestion 실행 경로 및 어댑터 테스트 구성
- Supabase 연동 검증
  - pooler DSN으로 DB 연결 성공
  - 수동 마이그레이션 적용 및 실제 update 실행 확인
- 운영자용 대시보드/수동 실행 기능 구현
  - run history 저장 및 조회
  - CLI 수동 실행 경로 추가
  - Streamlit 기반 운영 대시보드 앱 추가
- 품질 검증
  - 테스트 스위트 통과 (`37 passed`)
- 협업/배포 파이프라인
  - GitHub org 저장소 생성 및 푸시
  - 기능 브랜치/PR 생성 완료
  - Vercel 프로젝트 생성 및 레포 연결 완료

## 2) 현재 상태

- PR: `https://github.com/finance-flow-labs/finance-flow-labs/pull/1`
- Vercel 프로젝트: `finance-flow-labs-dashboard`
- 배포 URL: `https://finance-flow-labs-dashboard-63qomahwr-gwangwonchois-projects.vercel.app`
- Vercel 프로젝트 보호 설정 변경 완료
  - 기존: `ssoProtection.deploymentType=all_except_custom_domains`
  - 현재: `ssoProtection=null`
- 보호 이슈(401)는 해소되었고, 현재 응답은 `404 NOT_FOUND`

## 3) 남은 핵심 작업

1. 배포 런타임 정렬
   - 현재 Streamlit 앱은 Vercel 기본 라우팅에서 즉시 서비스되지 않아 루트 404 발생
   - Vercel 친화 런타임(예: Next.js/Flask API 라우트)로 노출하거나,
     Streamlit 전용 호스팅(Streamlit Community Cloud/Render)으로 분리 결정 필요
2. 최종 공개 접근 검증
   - 비로그인 상태에서 대시보드 URL 200 응답 검증
3. 운영 문서 마감
   - 최종 배포 구조와 수동 실행 절차(runbook) 업데이트

## 4) 권장 의사결정

- 단기(빠른 공개 확인 우선)
  - Vercel에는 최소 운영 API/상태 페이지를 배포하고,
  - Streamlit UI는 Streamlit 전용 호스팅으로 분리
- 중기(단일 배포 채널 선호)
  - 대시보드를 Next.js 기반으로 전환해 Vercel에 일원화

## 5) 재현/검증에 사용한 핵심 명령

- 프로젝트 조회
  - `vercel api "/v9/projects/finance-flow-labs-dashboard" --raw`
- 보호 설정 해제
  - `printf '%s' '{"ssoProtection":null}' | vercel api "/v9/projects/finance-flow-labs-dashboard" -X PATCH --input - --raw`
- 배포 접근 확인
  - `curl -s -i "https://finance-flow-labs-dashboard-63qomahwr-gwangwonchois-projects.vercel.app"`

## 6) 다음 세션 시작 체크리스트

- [ ] 대시보드 호스팅 방식 결정(Vercel 일원화 vs Streamlit 분리)
- [ ] 결정된 방식으로 배포 경로 수정
- [ ] 퍼블릭 200 응답 검증
- [ ] PR 본문/문서 최신화 후 병합 준비

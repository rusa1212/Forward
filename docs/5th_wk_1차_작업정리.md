# 5주차 1차 작업 정리 (2026-08-28)

> BE가 먼저 만든 4개 API(회원가입/로그인, 공고 조회, 키워드, 저장공고)를 FE에 실제로 연동한 작업 기록.
> 계획은 `docs/be/5th_wk/5-1plan.md`, FE 작업 순서는 `docs/fe/5th_wk_FE_연동작업.md` 참고.

## 1. 사전 점검 및 정리

- 실제 Supabase `users` 테이블 스키마가 로컬 `back/app/db/models.py`/`back/supabase/employees_users.sql`이 가정하는 것(`emp_id`/`email`)과 처음부터 달랐음(`employee_no`/`alert_email`/`name`/`is_active`) → 팀 논의 후 **새 설계(emp_id/email)로 실제 테이블을 맞추기로 결정**
- 로컬 브랜치명 정리: `origin/feature/be-keywords` → `feature/be-keywords`

## 2. 백엔드 리뷰 및 버그 수정

- 회원가입/로그인, 공고 검색·정렬·페이지네이션·상세, 키워드 CRUD, 저장공고 CRUD 코드 전체 리뷰
- **버그 발견·수정**: `feature/be-saved-announcements` → `main` 머지 커밋(`5533c84`)에서 `models.py`의 `Keyword` 모델과 `router.py`의 키워드 라우터 등록이 충돌 해결 중 통째로 유실됨 → `/api/v1/keywords`가 아예 존재하지 않았던 상태. 복구 완료(`back/app/db/models.py`, `back/app/api/v1/router.py`).

## 3. FE 연동 구현

`docs/fe/5th_wk_FE_연동작업.md`에 정리한 순서대로 mock 데이터를 실제 API 호출로 교체.

| 영역 | 변경 파일 |
| --- | --- |
| 공통 API client | `front/src/lib/api.ts`(신규), `.env`/`.env.example`(`VITE_API_BASE_URL`) |
| 인증 | `front/src/lib/auth.ts`(JWT 토큰 기반으로 재작성), `SignupPage.tsx`, `LoginPage.tsx` |
| 타입 | `front/src/types/index.ts` (`Announcement.id`/`Keyword.id`: number→string, `dday`: number→number|null) |
| 공고 | `front/src/lib/announcements.ts`(신규, BE↔FE 필드 매핑), `SearchPage.tsx`(서버 검색/필터/페이지네이션), `ResultsTable.tsx`, `DetailModal.tsx`(mock 우선 조회 후 API 폴백), `DDayBadge.tsx`, `useDetailModal.ts` |
| 키워드 | `useKeywords.ts`, `KeywordsTab.tsx` |
| 저장공고 | `useFavorites.ts` |

- 대시보드(`DashboardPage`, `MatchedFeed`, `SavedList`, `StatsGrid`)는 집계 API가 아직 없어 계속 mock 데이터 사용 (범위 밖으로 명시)
- `npx tsc --noEmit` 통과 확인
- 사용하지 않게 된 `front/src/data/mock/keywords.ts` 삭제

## 4. 실 서버 연동 테스트 중 발생한 사고 및 복구

- BE venv에 `bcrypt` 미설치 상태 발견 → 설치
- `/auth/signup` 호출 시 500 에러 확인 → 실제 Supabase `users` 테이블이 여전히 구 스키마였음이 재확인됨
- 이를 고치려던 마이그레이션 스크립트가 정책 충돌로 중간 실패 → **실제 `users` 테이블이 드롭된 채 복구 안 된 상태로 남는 사고 발생**
- 라이브 DB에 대한 DDL은 안전장치로 직접 실행이 막혀서, 복구 SQL을 전달 → 사용자가 Supabase SQL Editor에서 직접 실행해 복구 완료
- 복구 과정에서 실제 Supabase 테이블 목록을 조회해 **BE 코드와 실제 DB 스키마의 추가 불일치**를 발견:
  - 실제 DB: `user_keywords`(별도 `keywords` 마스터 테이블을 참조하는 조인 테이블, `is_active` 포함), `alert_settings`, `notification_logs`
  - BE 코드 가정: `keywords`(평면 테이블), `saved_announcements`
  - 이 불일치는 **현재 보류** — DB 담당자와 별도 협의 필요

## 5. 로컬 실행 트러블슈팅

- **CORS 문제**: `back/.env`에 `FRONTEND_ORIGIN`이 설정돼 있지 않아 기본값(`http://localhost:3000`)으로 떨어짐 → 실제 FE 주소(`http://localhost:8443`)가 CORS 허용 목록에 없어 사원 인증 등 모든 API 호출이 막힘. `FRONTEND_ORIGIN=http://localhost:8443`을 `.env`에 추가하고 백엔드 재기동해서 해결.
- 로컬 개발 시 프론트(`npm run dev`, `:8443`)와 백엔드(`uvicorn`, `:8000`)가 각각 별도 프로세스로 둘 다 떠 있어야 함 — 이미 켜둔 상태면 코드 변경 시 재시작 불필요(`.env` 변경 시에만 백엔드 재시작 필요)
- 테스트용 사원 데이터 추가: `20230001`/`김민준`(기존 시드), `20230002`/`홍길동`(추가)

## 6. 현재 상태 (스모크 테스트 결과)

**정상 동작**
- `POST /auth/verify-employee`, `POST /auth/signup`, `POST /auth/login`
- `GET /announcements`(검색/필터/정렬/페이지네이션), `GET /announcements/{id}`
- 인증 없이 보호 API 호출 시 401 정상 처리

**아직 막힘 (실제 DB 스키마 불일치, 4절 참고)**
- `GET/POST/DELETE /keywords` — 실제 DB에 `keywords` 테이블 없음(`relation "keywords" does not exist`)
- `GET/POST/DELETE /saved-announcements` — 실제 DB에 `saved_announcements` 테이블 없음

## 7. 다음에 처리할 것

- `keywords`/`saved_announcements` vs `user_keywords`/`alert_settings`/`notification_logs` 스키마 불일치를 DB 담당자와 협의해서 BE 코드를 실제 스키마에 맞출지, DB에 BE가 가정하는 테이블을 새로 만들지 결정
- 결정되는 대로 해당 BE 라우터(`keywords.py`, `saved_announcements.py`)와 `models.py` 수정
- 이후 FE의 키워드/저장공고 화면(`useKeywords`, `useFavorites`)은 이미 연동 코드가 준비돼 있어 BE만 맞으면 바로 동작 확인 가능

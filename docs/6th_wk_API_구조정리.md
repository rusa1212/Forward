# Forward BE API 구조 정리 (멘토 검토용)

> 작성일 2026-08-31 · 기준 코드: `back/app/api/v1/*` (main 브랜치)
> 목적: 지금까지 구현된 API 전체를 한 번에 파악하고, 세부 수정사항 피드백을 받기 위한 문서입니다.

## 1. 한눈에 보기

- 스택: **FastAPI + SQLAlchemy 2.0 + Supabase(PostgreSQL)** — MySQL/MariaDB 전환 예정 (별도 문서)
- 공통 prefix: **`/api/v1`** (`back/app/api/v1/router.py`)
- 라우터 6개 / 경로 13개 (메서드 기준 16개)
- 자동 수집: APScheduler가 매일 06:00(기본, `.env`로 변경 가능)에 공공데이터포털 3종 API를 수집해 upsert (`back/app/core/scheduler.py`)

### 엔드포인트 전체 목록

| # | 메서드·경로 | 인증 | 설명 | 파일 |
|---|---|---|---|---|
| 1 | `GET /api/v1/health` | ✕ | 서버 생존 확인 | health.py |
| 2 | `GET /api/v1/health/db` | ✕ | DB 연결 확인 (`SELECT 1`) | health.py |
| 3 | `GET /api/v1/collect` | ✕ ⚠️ | 수집 미리보기 (저장 안 함) | collect.py |
| 4 | `POST /api/v1/collect` | ✕ ⚠️ | 3개 소스 수집 → announcements upsert | collect.py |
| 5 | `GET /api/v1/announcements` | ✕ | 목록: 검색·필터·정렬·페이지네이션 | announcements.py |
| 6 | `GET /api/v1/announcements/{id}` | ✕ | 공고 상세 (404 처리) | announcements.py |
| 7 | `POST /api/v1/auth/verify-employee` | ✕ | 사번+이름 사원 명부 대조 (가입 1단계) | auth.py |
| 8 | `POST /api/v1/auth/signup` | ✕ | 계정 생성 (서버에서 사원 인증 재확인) | auth.py |
| 9 | `POST /api/v1/auth/login` | ✕ | 사번+비밀번호 → JWT 발급 | auth.py |
| 10 | `POST /api/v1/auth/logout` | ✕ | stateless — FE 토큰 삭제 안내용 | auth.py |
| 11 | `GET /api/v1/keywords` · `POST /api/v1/keywords` | ✅ | 내 키워드 조회 / 등록 | keywords.py |
| 12 | `DELETE /api/v1/keywords/{id}` | ✅ | 내 키워드 삭제 | keywords.py |
| 13 | `GET /api/v1/saved-announcements` · `POST /api/v1/saved-announcements` · `DELETE /api/v1/saved-announcements/{announcement_id}` | ✅ | 저장공고 조회 / 저장 / 저장취소 | saved_announcements.py |

⚠️ = collect 엔드포인트는 현재 **인증이 없어 외부에서 누구나 호출 가능** — 4절 이슈 참고

## 2. 공통 규칙

### 응답 형식

```jsonc
// 성공 (단건·동작)
{ "success": true, "data": { ... } }

// 성공 (목록) — meta에 페이지 정보
{ "success": true, "data": [ ... ], "meta": { "total": 133, "page": 1, "page_size": 20 } }

// 오류 — 상태코드와 무관하게 동일 구조 (back/app/core/errors.py)
{ "success": false, "error": { "code": "DUPLICATE_EMAIL", "message": "이미 등록된 이메일입니다." } }
```

- Pydantic 검증 실패는 일괄 `422 VALIDATION_ERROR`
- 처리되지 않은 예외는 `500 INTERNAL_ERROR`
- CORS는 `.env`의 `FRONTEND_ORIGIN` 1개 origin만 허용

### 사용 중인 오류 코드

| HTTP | code | 발생 위치 |
|---|---|---|
| 400 | EMPLOYEE_NOT_FOUND / EMPTY_KEYWORD / INVALID_SORT / INVALID_STATUS_LABEL | signup, keywords, announcements |
| 401 | INVALID_CREDENTIALS / UNAUTHORIZED / INVALID_TOKEN | login, get_current_user |
| 404 | ANNOUNCEMENT_NOT_FOUND / KEYWORD_NOT_FOUND / SAVED_ANNOUNCEMENT_NOT_FOUND | 상세/삭제류 (타인 소유도 404로 응답해 소유권 노출 방지) |
| 409 | DUPLICATE_EMP_ID / DUPLICATE_EMAIL / DUPLICATE_KEYWORD / ALREADY_SAVED | signup, keywords, saved |

### 인증 방식

- `POST /auth/login` 성공 시 **JWT(HS256)** 발급 — payload `{sub: user_id, exp: 발급+24h}` (`JWT_EXPIRE_HOURS`)
- 보호 API는 `Authorization: Bearer <token>` 헤더 필수 → `get_current_user`(back/app/api/v1/auth.py)가 검증
- 회원가입은 2단계: ① verify-employee(사번+이름 명부 대조) → ② signup. **signup이 단독 호출돼도 서버가 명부를 재확인**하므로 FE 검증 우회 불가
- 비밀번호는 bcrypt 해시 저장. 로그인 실패 시 사번/비밀번호 어느 쪽이 틀렸는지 구분해 알려주지 않음

### 공고 목록 쿼리 파라미터 (`GET /announcements`)

| 파라미터 | 값 | 비고 |
|---|---|---|
| q | 검색어 | 제목 부분일치 (대소문자 무시) |
| status | 원본 상태값 | 소스마다 달라 사용 비권장 (K-Startup은 Y/N) |
| statusLabel | 접수중 / 접수예정 / 마감임박 / 마감 | 접수기간으로 서버가 계산한 정규화 상태. **마감임박 = 마감 3일 이내(임시 기준, 협의 필요)** |
| department | 기관/부서 | 정확히 일치 |
| source | kstartup / narajangteo / msit | 수집 출처 |
| sort | latest(기본) / deadline / title | deadline은 마감일 없는 공고를 뒤로 |
| page / page_size | 1~ / 1~100 (기본 20) | |

응답 행에는 원본 필드 외에 계산 필드 `statusLabel`, `dday`(마감까지 남은 일수, 정보 없으면 null) 포함.

## 3. FE–BE 계약 불일치 현황

`docs/fe/5th_wk_FE_연동작업.md` 1절에서 정리한 표 그대로입니다 (코드 대조 확인 완료):

| 항목 | FE 현재 (`types/index.ts` 등) | BE 실제 응답 | 필요한 조치 |
| --- | --- | --- | --- |
| id 타입 | `Announcement.id`, `Keyword.id` = `number` | UUID 문자열 | 둘 다 `string`으로 변경 |
| 키워드 필드명 | `Keyword.name` | `{id, keyword, createdAt}` | FE 필드명을 `keyword`로 맞추거나 매핑 함수 작성 |
| 키워드 부가기능 | `matchCount`, `dashboardAlert`, `emailAlert` | 없음 | 이번 범위 구현 불가 — UI에서 숨기거나 더미 표시. `alert_settings`는 BE P1 |
| 공고 필드 | `org`, `announcementType`, `field`, `postedDate`, `budget`, `contact`, `relatedKeywords` 등 | `source`, `external_id`, `title`, `department`, `reception_start/end`, `status`, `statusLabel`, `detail_url`, `summary`, `collected_at`, `dday` | FE 필드 상당수가 BE에 없음 — 실제 쓰는 필드만 남기고 정리, 또는 BE에 추가 요청 |
| 로그인 응답 | — | `{token, id, email}` (empId 없음) | 사번 표시가 필요하면 입력값 재사용 또는 BE에 empId 추가 |
| 인증 방식 | `sessionStorage` 플래그 | `Authorization: Bearer <JWT>` | `lib/auth.ts` 전면 재작성 |

## 4. 알려진 미해결 이슈 (피드백 요청 사항)

1. **DB 스키마 이원화** — Supabase에는 두 갈래 스키마가 존재했습니다.
   - BE 코드가 실제 사용하는 것: `employees`, `users(emp_id, email)`, `keywords(user_id, keyword)`, `saved_announcements`, `announcements` (`back/supabase/*.sql`)
   - DB 설계 단계에서 별도로 만든 것: `users(employee_no, alert_email…)`, 전역 `keywords` + `user_keywords`, `alert_settings`, `notification_logs`
   - → **BE 코드 스키마를 표준으로 확정**하고, alert_settings/notification_logs는 P1(알림 기능) 구현 시 BE 모델과 함께 추가하는 방향을 제안합니다. MySQL 전환 DDL도 BE 코드 기준으로 작성했습니다.
2. **대시보드 집계 API 미구현** — 오늘 신규/키워드 매칭/마감임박/저장공고 수 (BE P0 잔여 항목). FE 대시보드는 mock 유지 중.
3. **알림·이메일·마이페이지 API 미구현** — BE P1. `alert_settings`, `notification_logs` 테이블 신설 필요.
4. **collect 엔드포인트 무인증** — 운영 배포 전 내부용 시크릿 헤더나 관리자 인증 필요.
5. **마감임박 기준 3일** — announcements.py의 임시값. 팀/멘토 협의로 확정 필요.
6. **로그인 응답에 empId 미포함** — FE 헤더 표시용으로 추가할지 결정 필요.
7. **DB 전환(Supabase→MySQL/MariaDB) 진행 중** — Postgres 전용 코드(UUID 타입, upsert 문법, timestamptz) 교체 작업. 상세는 `docs/be/6th_wk_DB전환.md` 참고.

## 5. 참고: 수집 파이프라인

- 소스 3종 (공공데이터포털, `DATA_GO_KR_API_KEY` 공용): 창업진흥원 K-Startup 사업공고(XML) / 조달청 나라장터 입찰공고(JSON) / 과기정통부 사업공고(JSON)
- 정규화 후 `announcements`에 **(source, external_id) UNIQUE 기준 upsert** → 재수집해도 중복 없음
- 수동 트리거: `POST /api/v1/collect` (미리보기는 GET) · 자동: 매일 06:00 스케줄러

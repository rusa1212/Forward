# 5주차 BE 구현 정리 (2026-08-27)

> `docs/be/5th_wk_BE_계획.md`의 Phase 0 ~ P0-8을 `back/`에 구현한 내역입니다.
> 테스트 96개 통과 (`cd back && .venv\Scripts\python -m pytest`).

## 결과 요약

| 항목 | 계획 | 상태 |
|---|---|---|
| Phase 0 | 기반 정비 (의존성·설정·보안·에러·모델·DDL) | 완료 |
| 4장 | 기존 코드 이슈 4건 수정 | 완료 |
| P0-1 | 회원가입 | 완료 |
| P0-2 | 인증/세션 (JWT) | 완료 |
| P0-3 | 공고 조회/검색/상세 | 완료 |
| P0-4 | 키워드 CRUD | 완료 |
| P0-5 | 저장공고 CRUD | 완료 |
| P0-6 | 대시보드 집계 | 완료 |
| P0-7 | 키워드 매칭 | 완료 (스케줄러에 연결) |
| P0-8 | 품질 (예외·로깅·Swagger·테스트) | 완료 |
| P1-9~11 | 마이페이지 / 알림·이메일 / 스케줄러 백필 | **미착수** |

## 확정된 결정사항

**인증 방식 — 자체 bcrypt 해시 + JWT** (계획 2-1의 권장안). 로그인 ID가 사번이라
Supabase Auth의 이메일 기반 흐름을 우회할 필요가 없어졌고, 등록 이메일 원본이
`users` 테이블 한 곳이라 Auth ↔ 프로필 동기화 문제도 발생하지 않습니다.

- 비밀번호: `bcrypt` 직접 사용 (passlib 대신 — passlib 1.7.4 + bcrypt 5.x 호환 경고 회피).
  72바이트 초과 입력은 조용히 잘리지 않도록 거부합니다.
- 토큰: `pyjwt` HS256, 기본 만료 8시간(`ACCESS_TOKEN_EXPIRE_MINUTES`).
  로그아웃은 FE가 토큰을 폐기하는 방식이고 블랙리스트는 없습니다.
- **RLS는 2차 방어선**입니다. BE가 `DATABASE_URL`(서비스 계정)로 접속해 RLS를 우회하므로,
  개인화 쿼리는 전부 `user_id` 조건을 강제합니다. 사용자 간 격리는 테스트로 검증했습니다
  (`test_keywords.py`, `test_saved.py`의 격리 테스트 7건).

## 추가된 구조

```
app/
  core/security.py          bcrypt 해시 + JWT 발급/검증
  core/errors.py            ErrorCode + AppError + 예외 핸들러 4종
  api/deps.py               get_current_user / get_current_user_optional
  schemas/                  common, auth, announcement, keyword, saved, dashboard
  services/                 auth, announcement, keyword, saved, matching, dashboard
  api/v1/                   auth.py, me.py, dashboard.py (+ announcements.py 확장)
sql/week5_schema.sql        5주차 DDL
tests/                      96개 (auth 14 / announcements 25 / keywords 15 / saved 13 /
                            dashboard 17 / quality 12)
```

## DB 스키마 — `back/sql/week5_schema.sql`

Supabase SQL Editor에서 한 번 실행해야 합니다. `IF NOT EXISTS`라 재실행 안전.

1. `announcements.org` 컬럼 추가 — 수집 결과의 `agency`를 담을 자리가 없어 `department`에
   밀어넣고 있었습니다. 이제 `org`에 기관, `department`에 부서가 들어갑니다.
2. `users` — `employee_no`(unique), `name`, `email`(unique), `password_hash`, `email_alert_enabled`
3. `user_keywords` — `UNIQUE(user_id, keyword)`
4. `saved_announcements` — `UNIQUE(user_id, announcement_id)`
5. `notification_logs` — `UNIQUE(user_id, announcement_id, type)`, `matched_keywords`, `read_at`, `emailed_at`
6. 인덱스 6종 + 제목 부분검색용 `pg_trgm` GIN 인덱스 (DB 파트 P1 항목을 미리 포함)
7. RLS enable (정책 없음 → anon/authenticated 전면 차단, service_role만 통과)

ORM 모델(`app/db/models.py`)은 이 DDL과 1:1입니다. 타입은 방언 중립적
(`sqlalchemy.Uuid`, `func.now()`)으로 두어 SQLite 테스트가 가능하게 했습니다.

## 기존 코드에서 고친 것 (계획 4장)

| 항목 | 내용 |
|---|---|
| 4-1 CORS | 단일 오리진 → `CORS_ORIGINS` 콤마 목록. 기본값에 8443 포함 (기존엔 3000만 있어 FE가 막혔을 것) |
| 4-2 upsert | 배치 내 `(source, external_id)` 중복을 선제거. 그대로면 페이지네이션 경계에서 `ON CONFLICT DO UPDATE cannot affect row a second time`으로 **수집 전체가 실패**했습니다 |
| 4-3 저장 건수 | `len(rows)` → `RETURNING xmax = 0`으로 `{inserted, updated, skipped, duplicates_in_batch}` 반환 |
| 4-4 신규 판별 | `collected_at`이 upsert에서 갱신되지 않는다는 점을 "오늘 신규"의 기준으로 확정하고 모델·storage·README 3곳에 주석으로 고정 |

4-5(나라장터 수집 구간이 오늘 하루 고정 → 실행 실패 시 해당일 누락)는 **미해결**입니다.
P1-11 스케줄러 백필과 함께 처리해야 합니다.

## 핵심 설계 — 파생 필드 단일 출처

`status`와 `dday`는 DB 컬럼이 아니라 계산값입니다. 소스별 원본 상태값
(`Y/N`, `일반경쟁`, `null`)이 제각각이라 표시에 쓸 수 없어서, 마감일 기준으로 재계산합니다.

- 판정 우선순위: **마감 > 접수예정 > 마감임박 > 접수중**
- 마감임박 기준: `DEADLINE_SOON_DAYS`(기본 7일). 대시보드·검색 필터·알림이 이 값을 공유합니다.
- 마감일이 없는 공고(msit)는 `status`/`dday` 모두 `null`

규칙은 `announcement_service.py`에만 있고, 파이썬 계산(`compute_status`)과
SQL 필터(`status_condition`)가 갈라지지 않도록 **두 구현의 판정이 일치하는지 테스트로 검증**합니다
(`test_sql_status_filter_matches_python_computation`). 이 둘이 어긋나면 검색 결과와 화면 배지가
따로 놀게 됩니다.

직렬화도 `to_summary()` 한 곳을 거치므로 공고 목록·상세·저장공고·대시보드의 표시값이 항상 같습니다.

## 엔드포인트 (21개)

전체 목록과 에러 코드 표는 `back/README.md` 참고. 인증 필요 표시는 🔒.

- 인증: `POST /auth/signup`, `POST /auth/login`, `GET /auth/me` 🔒, `POST /auth/logout` 🔒
- 공고: `GET /announcements`(인증 선택), `GET /announcements/{id}`(인증 선택)
- 키워드 🔒: `GET|POST /me/keywords`, `PATCH|DELETE /me/keywords/{id}`
- 저장공고 🔒: `GET|POST /me/saved`, `DELETE /me/saved/{announcement_id}`
- 대시보드 🔒: `GET /dashboard/summary|matched|saved|overview`
- 기존: `GET /health`, `GET /health/db`, `GET|POST /collect`

`/dashboard/overview`는 통계+매칭+저장을 한 번에 주는 추가 엔드포인트입니다.
FE가 첫 화면에서 요청 3개를 보내지 않아도 됩니다.

## 키워드 매칭 (P0-7)

두 경로로 나눴습니다.

1. **조회용** — 사용자 키워드로 즉석 필터(ILIKE). 대시보드 매칭공고와 공고 목록의
   `related_keywords`가 사용합니다. 항상 최신이라 동기화가 필요 없습니다.
2. **알림용** — `create_match_notifications()`가 신규 공고 × 사용자 키워드 결과를
   `notification_logs`에 적재. `UNIQUE(user_id, announcement_id, type)`로 중복 알림을 막고,
   재실행해도 새로 생성되지 않습니다(멱등성 테스트 포함).

매칭 방식은 제목·요약 부분일치입니다. 형태소 분석은 범위 밖.

스케줄러(`core/scheduler.py`)를 **수집 → upsert → 매칭 알림 생성**으로 확장하고
단계별 예외를 격리했습니다. 매칭이 실패해도 수집 결과는 저장된 상태로 남습니다.

## 품질 (P0-8)

- **응답 규약 통일** — 성공 `{success, data}` / 실패 `{success, error:{code, message, details}}`.
  404·405·422·500과 도메인 예외가 모두 같은 형태로 나옵니다.
- **500 응답에 스택트레이스 미노출** — 서버 로그에만 기록. 테스트로 검증.
- **로깅** — 요청 단위 접근 로그(메서드/경로/상태/소요시간). 본문과 Authorization 헤더는
  기록하지 않으며, 비밀번호·토큰이 로그에 남지 않는지 테스트로 검증합니다.
- **Swagger** — 전 엔드포인트에 summary/description, Bearer 인증 스키마 등록.
  "summary 없는 엔드포인트가 없다"를 테스트로 강제해서 FE가 Swagger만 보고 붙을 수 있게 했습니다.
- **테스트 96개** — SQLite 인메모리. Postgres 전용 기능을 쓰는 `storage.py`는 제외
  (실제 Supabase 연결로 확인해야 하는 부분입니다).

## 남은 일 / 다른 파트 확인 필요

**실행 전 필수**
1. `back/sql/week5_schema.sql`을 Supabase에서 실행 (DB 파트)
2. `back/.env` 작성 — `DATABASE_URL`, `DATA_GO_KR_API_KEY`, `JWT_SECRET`(prod 필수)
3. 실제 Supabase 연결로 `POST /api/v1/collect` 재확인 — `org` 컬럼 추가와
   upsert 반환값 변경이 실DB에서 동작하는지는 아직 검증하지 못했습니다

**미확정 항목**
| 항목 | 현재 구현 | 확인 대상 |
|---|---|---|
| 사번 형식 | 영문/숫자 4~20자 (`schemas/auth.py`의 `EMPLOYEE_NO_PATTERN`) | DB 파트 — 실제 규칙 확정되면 패턴만 교체 |
| 마감임박 기준 | D-7 (`DEADLINE_SOON_DAYS=7`) | PM |
| 분야(`field`) 필터 | 미구현 (외부 API에 데이터 없음) | PM — 5주차 제외 승인 |
| 중복 저장 응답 | 409 `ALREADY_SAVED` | FE — 멱등 200을 원하면 변경 |

**FE 작업 필요**
1. `Announcement.id`를 `number` → `string`(uuid)
2. `src/lib/auth.ts`의 sessionStorage 플래그 → `Authorization: Bearer <token>` 방식으로 교체
3. `status`/`dday`가 `null`일 수 있음 (마감일 없는 공고) — 화면에서 "-" 처리 필요
4. `field` / `announcementType` 필터 비활성
5. 개발 서버 포트 확정 → `CORS_ORIGINS`에 반영 (현재 8443, 3000 둘 다 허용)

**P1 미착수**: 마이페이지(9), 알림/이메일(10), 스케줄러 백필(11)

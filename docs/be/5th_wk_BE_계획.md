# 5주차 BE 작업 계획 (2026-08-27)

> 기준 문서: `5주차_파트별_작업_우선순위.md` BE 표(1~11번)
> 현재 코드 기준: `back/` (4주차 완료분 — Supabase 연결, 외부 API 수집, upsert, APScheduler)

---

## 1. 현재 상태 (4주차 종료 시점)

| 구분 | 상태 |
|---|---|
| FastAPI 앱 + CORS + lifespan | 있음 (`app/main.py`) |
| Supabase 접속 (SQLAlchemy) | 있음 (`app/db/session.py`) |
| ORM 모델 | `Announcement` **1개만** |
| 라우터 | `health`, `collect`, `announcements`(단순 목록) |
| 인증 | **없음** (FE는 `sessionStorage` 플래그로 데모 로그인) |
| 개인화(키워드/저장공고) | **없음** (FE는 `src/data/mock/*` 목데이터 + Context) |
| 자동 수집 | 있음 (매일 06:00, 3개 소스) |

즉 5주차 BE 작업 11건 중 **인증·개인화·대시보드·알림은 0에서 시작**이고, 공고 조회(3번)만 단순 목록 조회가 있는 상태에서 확장하는 형태입니다.

---

## 2. 착수 전 확정해야 할 결정사항

### 2-1. 인증 방식 — Supabase Auth vs 자체 해시+JWT (가장 먼저 결정)

우선순위 문서는 "Supabase Auth 또는 안전한 해시 방식"으로 둘 다 허용하고 있는데, **로그인 ID가 이메일이 아니라 사번**이라는 점이 갈림길입니다.

| 방식 | 장점 | 단점 |
|---|---|---|
| **자체 해시 + JWT (권장)** | 사번 로그인이 자연스러움. 이미 있는 SQLAlchemy/FastAPI 스택으로 끝남. BE가 전 과정 통제 | 비밀번호 정책·재설정·토큰 만료를 직접 구현. RLS와 연동하려면 Supabase JWT secret으로 서명 필요 |
| Supabase Auth | 해시·세션·이메일 인증을 위임 | 사번 로그인이 `사번 → 이메일` 선조회 후 `signInWithPassword` 2단계가 됨. `supabase-py` 의존성 추가. 프로필 테이블과 Auth 유저 동기화 부담 |

**권장: 자체 해시(bcrypt) + JWT.** 5주차 남은 기간과 현재 스택을 고려하면 구현·디버깅 비용이 가장 낮습니다.

이 결정에 따라오는 것:

- DB의 RLS(DB 파트 P0 3번)는 **BE가 `DATABASE_URL`로 Postgres에 직접 접속**하는 구조에서는 우회됩니다(서비스 계정 접속). 따라서 **RLS는 2차 방어선**으로 두고, 사용자별 데이터 격리는 **애플리케이션 계층에서 모든 쿼리에 `user_id` 조건을 강제**하는 방식으로 보장해야 합니다. → DB 파트와 이 전제를 반드시 합의.

### 2-2. FE `Announcement` 타입과 DB 스키마의 불일치

`front/src/types/index.ts`가 기대하는 필드 중 DB `announcements`에 **없는 것**:

| FE 필드 | DB 대응 | 처리 방안 |
|---|---|---|
| `id: number` | `id: uuid` | **FE를 `string`으로 변경** 권장 (DB 변경보다 저렴) |
| `org` (기관) | 없음 (`department`만) | 수집 결과의 `agency`를 담을 `org` 컬럼 추가 요청 |
| `field` (분야) | 없음 | 분류 규칙 필요 → **5주차는 필터 비활성**으로 축소 제안 |
| `announcementType` / `announceType` | 없음 | 동일. 축소 대상 |
| `budget`, `contact`, `projectName` | 없음 (`summary`에 원문) | 상세 API에서 `summary`로 대체, 나머지는 null |
| `status` | 있으나 소스별 값이 제각각 | **BE가 마감일 기준으로 재계산**해서 4종(접수예정/접수중/마감임박/마감)으로 정규화 |
| `dday` | 없음 | BE 계산 필드로 응답에 포함 |
| `relatedKeywords` | 없음 | 사용자 키워드 매칭 결과로 산출 |

→ **BE·FE·DB 3자 합의가 필요하며, P0-3(공고 조회) 착수 전에 끝나야 합니다.** 미확정 필드는 응답에 `null`로 내려 FE가 먼저 붙을 수 있게 하는 것을 권장.

### 2-3. 분야(`field`) 분류를 5주차 범위에 넣을지

외부 API에 분야 필드가 없어 자체 분류(키워드 규칙 또는 LLM)가 필요합니다. **5주차 범위에서 제외하고 6주차 이후로 미루는 것을 권장** — 검색 필터 중 "분야"만 비활성화.

---

## 3. 사전 정비 작업 (Phase 0, 0.5일)

본 작업 11건 전부의 선행조건입니다.

1. **의존성 추가** (`back/requirements.txt`)
   - `passlib[bcrypt]` (비밀번호 해시), `pyjwt` (JWT), `email-validator` (이메일 검증), `pytest` (테스트)
2. **폴더 구조 확장**
   ```
   app/
     core/security.py       비밀번호 해시/검증, JWT 발급/디코드
     core/errors.py         공통 에러 코드 + 예외 핸들러
     api/deps.py            get_current_user (HTTPBearer)
     schemas/               Pydantic 요청/응답 모델 (auth, announcement, keyword, saved, dashboard)
     services/              announcement_service, keyword_service, saved_service, dashboard_service, matching_service
     api/v1/                auth.py, me.py, dashboard.py (+ 기존 announcements.py 확장)
   ```
3. **ORM 모델 추가** (`app/db/models.py`) — DB 파트가 확정한 실제 테이블과 1:1
   - `User` — `id(uuid)`, `employee_no(unique)`, `name`, `email(unique)`, `password_hash`, `created_at`
   - `UserKeyword` — `id`, `user_id(FK)`, `keyword`, `dashboard_alert`, `email_alert`, `created_at`, `UNIQUE(user_id, keyword)`
   - `SavedAnnouncement` — `id`, `user_id(FK)`, `announcement_id(FK)`, `created_at`, `UNIQUE(user_id, announcement_id)`
   - `NotificationLog` — `id`, `user_id(FK)`, `announcement_id(FK)`, `type`(match/deadline), `sent_at`, `read_at`, `UNIQUE(user_id, announcement_id, type)`
4. **공통 응답 규약 확정** — 기존 `{success, data}` 유지 + 실패 시 `{success:false, error:{code,message,details}}`로 통일. `RequestValidationError`/`HTTPException` 핸들러를 `main.py`에 등록.
5. **환경변수 추가** — `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`. `.env.example`도 갱신.
6. **CORS 다중 오리진화** — 아래 4-1 참고.

---

## 4. 착수 전 고쳐야 할 기존 코드 이슈

작업 중 발견한 실제 결함입니다. Phase 0에서 함께 처리하는 것을 권장합니다.

### 4-1. CORS 오리진 불일치 + 단일값 (높음)

`app/core/config.py:14`의 기본값은 `http://localhost:3000`이지만, `AGENTS.md`가 명시한 FE 개발 서버 포트는 **8443**입니다. 또 `app/main.py:22`의 `allow_origins=[settings.FRONTEND_ORIGIN]`은 값 하나만 받습니다.
→ 콤마 구분 문자열을 리스트로 파싱하도록 바꾸고, 기본값에 실제 포트를 반영. FE가 인증을 붙이는 순간 바로 막히는 부분이라 우선 처리.

### 4-2. 같은 배치 안에 중복 키가 있으면 upsert가 예외 (중간)

`app/services/storage.py`의 `insert(...).on_conflict_do_update(...)`는 **하나의 INSERT 문 안에 `(source, external_id)`가 중복된 행이 있으면** Postgres가 `ON CONFLICT DO UPDATE command cannot affect row a second time` 오류를 냅니다. 페이지네이션 경계에서 같은 공고가 두 번 들어오면 수집 전체가 실패합니다.
→ `rows`를 `(source, external_id)` 기준으로 선(先)중복제거.

### 4-3. `saved` 반환값이 실제 저장 건수가 아님 (낮음)

같은 파일의 `return len(rows)`는 시도한 행 수입니다. 신규/갱신 구분이 안 되므로 대시보드의 "오늘 신규"에 재사용할 수 없습니다.
→ `RETURNING` + `xmax = 0` 판별로 insert/update를 분리하거나, 신규 판별은 `collected_at`으로 처리(4-4 참고).

### 4-4. "신규 공고" 판별 기준 확정 (중간)

현재 upsert의 `set_`에 `collected_at`이 없어서 **`collected_at`은 최초 삽입 시각이 유지**됩니다. 이건 오히려 유리해서 **"오늘 신규 = `collected_at::date = today`"**로 쓸 수 있습니다. 다만 의도한 동작인지 확인하고 **주석/문서로 고정**해야 합니다(누군가 `collected_at`을 갱신 대상에 넣으면 대시보드와 알림이 동시에 깨짐).

### 4-5. 나라장터 수집 구간이 "오늘 하루" 고정 (중간)

`today_bid_date_range()`가 항상 오늘 00:00~23:59이므로, 스케줄러가 하루 실패하면 그 날 공고는 **영구 누락**됩니다.
→ 자동화(P1-11) 작업 시 최근 N일 백필 또는 실패 재시도를 함께 설계.

---

## 5. P0 작업 계획 (우선순위 문서 1~8번)

### P0-1. 회원가입 (문서 1번) — 0.5일

**`POST /api/v1/auth/signup`**

- 요청: `employee_no`, `name`, `email`, `password`
- 검증: 사번 형식(DB 파트와 규칙 합의 — 자리수/숫자 여부), 이메일 형식, 비밀번호 정책(8자 이상 등)
- 처리: `passlib` bcrypt 해시 → `users` INSERT. **평문 저장 금지, 로그에도 비밀번호 미출력.**
- 중복: 사번/이메일 중복 시 `409` + 어느 쪽이 중복인지 구분되는 에러 코드(`DUPLICATE_EMPLOYEE_NO` / `DUPLICATE_EMAIL`) — FE가 필드별 에러를 표시할 수 있어야 함
- DB UNIQUE 제약의 `IntegrityError`도 잡아서 409로 변환(경합 대비)
- 응답에 `password_hash` 절대 미포함
- **완료 확인:** Swagger로 가입 → Supabase `users` 조회 → 같은 사번 재가입 시 409

### P0-2. 인증/세션 (문서 2번) — 0.5일

- **`POST /api/v1/auth/login`** — `employee_no` + `password` → `access_token`(JWT, `sub=user_id`), `token_type`, `expires_in`
- **`GET /api/v1/auth/me`** — 토큰으로 내 정보 조회
- **`POST /api/v1/auth/logout`** — 토큰 방식이므로 서버는 성공 응답만(FE가 토큰 폐기). 블랙리스트는 5주차 범위 외
- **`app/api/deps.py: get_current_user`** — `HTTPBearer`로 토큰 파싱 → 만료/서명오류 `401`, 유저 없음 `401`
- 로그인 실패는 **사번 오류/비밀번호 오류를 구분하지 않고** 동일한 401 메시지(계정 열거 방지)
- **완료 확인:** 가입 계정으로 로그인 → 토큰으로 보호 API 200, 토큰 없이 401, 만료 토큰 401

### P0-3. 공고 조회/검색/상세 (문서 3번) — 1일

- **`GET /api/v1/announcements`**
  - 파라미터: `q`(제목·요약 검색), `status`, `source`, `department`, `deadline_from/to`, `page`, `size`, `sort`(`deadline|latest`)
  - 응답: `{items, page, size, total, total_pages}` — FE `Pagination.tsx`가 요구
  - 인증 불필요(또는 선택) — 단, 토큰이 있으면 `is_favorite` 포함
- **`GET /api/v1/announcements/{id}`** — 상세. `DetailModal.tsx`가 쓰는 필드 기준
- **파생 필드 계산 서비스** (`announcement_service.py`)
  - `dday = reception_end - today`
  - `status` 재계산: `reception_start > today` → 접수예정 / `dday < 0` → 마감 / `0 <= dday <= 7` → 마감임박 / 그 외 접수중 (임계값은 PM 확인)
- 검색은 우선 `ILIKE`로 구현, 성능 이슈 시 DB 파트에 인덱스(P1) 또는 `tsvector` 요청
- **선행:** 2-2 필드 매핑 합의
- **완료 확인:** FE 검색 화면이 목데이터 없이 실데이터로 동작

### P0-4. 키워드 CRUD (문서 4번) — 0.5일

- **`GET /api/v1/me/keywords`** — 내 키워드 목록. FE `Keyword` 타입에 맞춰 `match_count`(해당 키워드 매칭 공고 수), `dashboard_alert`, `email_alert` 포함
- **`POST /api/v1/me/keywords`** — `{keyword}`. 정규화(trim + 대소문자 무시 비교) 후 중복 시 `409`
- **`DELETE /api/v1/me/keywords/{id}`** — **본인 소유 확인 후 삭제** (남의 것 → 404)
- **`PATCH /api/v1/me/keywords/{id}`** — 알림 토글 (FE `KeywordsTab.tsx`에 토글 UI 존재)
- 모든 쿼리에 `user_id` 조건 강제
- **완료 확인:** 등록 → 재로그인 후에도 조회됨 → 삭제 반영

### P0-5. 저장공고 CRUD (문서 5번) — 0.5일

- **`GET /api/v1/me/saved`** — 저장공고 목록(공고 상세 join, 페이지네이션)
- **`POST /api/v1/me/saved`** — `{announcement_id}`. 존재하지 않는 공고 `404`, 중복 저장 `409`(또는 멱등 200 — FE와 합의)
- **`DELETE /api/v1/me/saved/{announcement_id}`** — 저장 취소
- **완료 확인:** 저장 → 새로고침/재로그인 후 유지 → 취소 반영

### P0-6. 대시보드 집계 (문서 6번) — 0.5일

- **`GET /api/v1/dashboard/summary`** → `{today_new, matched_count, deadline_soon, saved_count}`
  - `today_new`: `collected_at::date = today` (4-4 참고)
  - `matched_count`: 내 키워드 매칭 공고 수
  - `deadline_soon`: `0 <= dday <= 7`
  - `saved_count`: 내 저장공고 수
- **`GET /api/v1/dashboard/matched`** — 오늘 매칭 공고 목록 (FE `MatchedFeed.tsx`)
- **`GET /api/v1/dashboard/saved`** — 저장공고 요약 목록 (FE `SavedList.tsx`)
- 4개 집계를 **개별 요청으로 나누지 말고** 한 응답으로 묶어 처리(대시보드 첫 화면 지연 방지)
- **완료 확인:** `StatsGrid` 4개 카드가 실데이터 표시

### P0-7. 키워드 매칭 (문서 7번) — 0.5일

- **`app/services/matching_service.py`**
  - `match_keywords_for_user(db, user_id)` — 내 키워드 vs 공고 `title`/`summary` 매칭
  - `match_new_announcements(db)` — 신규 공고 × 전체 사용자 키워드 → 매칭 결과 생성
- 매칭 방식: 1단계는 `ILIKE`. 형태소 분석은 범위 외
- 결과 저장: `notification_logs`에 `(user_id, announcement_id, 'match')` UNIQUE로 **중복 알림 방지**
- 공고 응답의 `related_keywords`도 이 서비스에서 산출
- **완료 확인:** 키워드 등록된 사용자에게 매칭 공고가 생성되고, 재실행 시 중복 생성 안 됨

### P0-8. 품질 — 예외/로그/API 테스트 (문서 8번) — 1일

- **예외 처리 통일** — 4xx/5xx 응답 스키마 일관화, 스택트레이스 노출 금지
- **로깅** — 요청 단위 로그(메서드/경로/상태코드/소요시간). 비밀번호·토큰 마스킹. `logging` 설정을 `main.py`에 집중
- **Swagger 정리** — 태그, 요약, 요청/응답 예시, Bearer 인증 스키마 등록 → FE가 Swagger만 보고 붙을 수 있는 수준
- **API 테스트** — `pytest` + `TestClient`로 회원가입→로그인→키워드→저장공고→대시보드 해피패스 + 인증 실패/중복/404 케이스. 최소한 Postman 컬렉션이라도 산출물로 남길 것
- **FE 연동 이슈 대응** — 필드명/타입/CORS/토큰 헤더 불일치 수정 버퍼
- **완료 확인:** FE가 목데이터 제거하고 전 화면 연동 가능

---

## 6. P1 작업 계획 (문서 9~11번)

P0 완료 후 여력이 있을 때. 순서는 9 → 10 → 11 (10번이 9번의 알림설정에 의존).

### P1-9. 마이페이지 (0.5일)

- `GET/PATCH /api/v1/me` — 이름, 이메일 조회·수정. 이메일 변경 시 중복 검증(409)
- `POST /api/v1/me/password` — 현재 비밀번호 검증 후 변경
- `GET/PUT /api/v1/me/notification-settings` — 알림 설정
- **참고:** 우선순위 문서 마지막 경고(등록 이메일 이중 보관) 관련 — 자체 인증을 택하면 이메일 원본은 `users` 한 곳이라 동기화 문제가 애초에 발생하지 않음. Supabase Auth를 택하면 Auth와 프로필 양쪽 동기화 로직이 추가로 필요.

### P1-10. 알림/이메일 (0.5~1일)

- 알림 생성: 신규 매칭 + 마감임박(D-7/D-3 등)
- 이메일 발송: SMTP(또는 Resend/SendGrid) — 발송 실패 재시도 정책 필요
- 발송 이력 `notification_logs`에 기록, UNIQUE로 중복 발송 차단
- `GET /api/v1/me/notifications`, `PATCH .../{id}/read` — FE `AlertsDropdown.tsx`용
- 환경변수 추가(SMTP 계정)

### P1-11. 자동화 스케줄러 확장 (0.5일)

- 기존 `run_daily_collect`에 후속 단계 연결: **수집 → upsert → 신규 판별 → 키워드 매칭 → 알림 생성 → 이메일 발송**
- 각 단계 실패가 다음 단계를 막지 않도록 단계별 예외 격리 + 로그
- 4-5(수집 구간 백필)를 여기서 함께 해결
- 실행 이력 테이블 또는 로그로 성공/실패 추적

---

## 7. 권장 진행 순서와 일정

`ⓐ`는 다른 파트 대기 없이 바로 착수 가능, `ⓑ`는 선행 합의 필요.

| 일자 | 작업 |
|---|---|
| **Day 1 오전** | ⓑ 결정사항 2-1(인증 방식)·2-2(필드 매핑) 확정 / ⓐ Phase 0 정비 + 4장 기존 이슈 수정 |
| **Day 1 오후** | ⓐ P0-1 회원가입, P0-2 인증 → **FE 언블록 (FE 1·2번이 이걸 기다림)** |
| **Day 2** | ⓐ P0-3 공고 조회/검색/상세 → **FE 3번 언블록** |
| **Day 3 오전** | ⓐ P0-4 키워드 CRUD |
| **Day 3 오후** | ⓐ P0-5 저장공고 CRUD → **FE 4번 언블록** |
| **Day 4 오전** | ⓐ P0-6 대시보드 집계 → **FE 5번 언블록** |
| **Day 4 오후** | ⓐ P0-7 키워드 매칭 |
| **Day 5** | ⓐ P0-8 품질/테스트/FE 연동 대응 (P0 마감) |
| **여력 시** | P1-9 → P1-10 → P1-11 |

**핵심 원칙: FE가 대기하는 순서대로 배포한다.** FE의 P0 5건이 전부 BE에 막혀 있으므로, 각 API는 완성 즉시(문서화 포함) FE에 알리고 다음 작업으로 넘어가는 편이 전체 일정에 유리합니다. 특히 **Day 1 오후의 로그인 API가 FE 전체의 최대 병목**입니다.

---

## 8. 다른 파트에 요청할 사항

**DB 파트 (선행 블로커)**

1. `users`(사번·이름·이메일·비밀번호해시), `user_keywords`, `saved_announcements`, `notification_logs` 테이블 확정 — 컬럼명·타입·NULL·UNIQUE·FK
2. `announcements`에 `org` 컬럼 추가 (FE 기관 표시용)
3. RLS를 적용하되, **BE는 서비스 계정으로 접속하므로 RLS를 우회한다**는 전제 공유 → 사용자 격리는 BE 쿼리에서 보장
4. 사번 형식 규칙(자리수·문자 허용 범위)
5. (P1) 검색·마감일·`user_id` 조회용 인덱스

**FE 파트**

1. `Announcement.id`를 `number` → `string`(uuid)로 변경
2. `field` / `announcementType` 필터는 5주차 비활성 (2-3 참고)
3. 인증은 `Authorization: Bearer <token>` 헤더 방식 — `src/lib/auth.ts` 교체 필요
4. 개발 서버 포트 확정(8443 vs 3000) → BE CORS 설정에 반영

**PM**

1. "마감임박" 임계값(D-7? D-3?) 확정 — 대시보드·검색 필터·알림 3곳에서 동일하게 사용
2. 2-3(분야 분류 5주차 제외)에 대한 범위 승인

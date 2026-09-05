# API 계약서 v1 (FE ↔ BE)

> **5-1plan.md 순서 1의 산출물.** 2026-08-28 작성 / 2026-09-05 갱신.
> 기준 코드: `origin/main`(`a47d968`). 갱신분은 실제 기동한 서버의 응답으로 검증했다
> (`docs/fe/6th_wk_E2E_리허설.md`).
> 이 문서가 FE·BE 간 유일한 기준이다. 코드와 다르면 **이 문서를 먼저 고치고** 코드를 맞춘다.
>
> **2026-09-05 갱신 내역** — 그동안 계약서에 없던 4개 영역을 추가했다: 7절 대시보드,
> 8절 마이페이지, 9절 알림, 10절 관리자. 기존 오류 코드 표는 11절, 요약은 12절로 밀렸다.
> DB는 6주차에 Supabase(Postgres) → MySQL/MariaDB로 전환됐고 스키마 정본은 `back/alembic/versions/`다.

---

## 1. 공통 규칙

### 1-1. Base URL

모든 엔드포인트는 `/api/v1` 하위에 둔다.

| 환경 | Base URL |
| --- | --- |
| 로컬 | `http://localhost:8000/api/v1` |
| FE 환경변수 | `VITE_API_BASE_URL` (`front/.env`) |

BE는 `FRONTEND_ORIGIN`(기본 `http://localhost:8443`)에 대해 CORS를 연다. FE를 다른 포트로 띄우면 `back/.env`를 함께 고친다.

### 1-2. 응답 포맷

**성공**

```json
{ "success": true, "data": <object | array> }
```

목록 응답은 `data`가 배열이고, 페이지네이션이 있으면 `meta`가 붙는다.

```json
{
  "success": true,
  "data": [ ... ],
  "meta": { "total": 137, "page": 1, "page_size": 20 }
}
```

**실패**

```json
{
  "success": false,
  "error": { "code": "DUPLICATE_EMAIL", "message": "이미 등록된 이메일입니다." }
}
```

- HTTP 상태 코드와 `error.code`를 함께 본다. **분기는 `error.code`로 하고, `error.message`는 그대로 화면에 띄워도 되는 한국어 문구다.**
- BE `back/app/core/errors.py`가 모든 예외를 이 포맷으로 감싼다. 처리 못 한 예외도 `500 INTERNAL_ERROR`로 나온다.

### 1-3. id 타입

**모든 리소스 id는 UUID 문자열(string)이다.** BE가 `str(uuid)`로 직렬화한다.
FE `front/src/types/index.ts`의 `Announcement.id`·`Keyword.id`를 `number` → `string`으로 고친다.

### 1-4. 인증

| 항목 | 값 |
| --- | --- |
| 방식 | JWT (HS256) |
| 발급 | `POST /auth/login` 응답의 `data.token` |
| 전달 | 요청 헤더 `Authorization: Bearer <token>` |
| payload | `sub` = user id(UUID 문자열), `exp` = 만료 시각 |
| 유효기간 | `JWT_EXPIRE_HOURS` (기본 24시간) |
| 로그아웃 | 서버는 상태를 갖지 않는다. **FE가 토큰을 지우면 로그아웃이다.** `POST /auth/logout`은 형식상 존재 |

**토큰이 필요한 엔드포인트**: `/keywords/*`, `/saved-announcements/*`
**토큰이 필요 없는 엔드포인트**: `/health/*`, `/auth/*`, `/announcements/*`

FE 공통 client는 `401`을 받으면 저장한 토큰을 폐기하고 로그인 화면으로 보낸다.

### 1-5. 날짜

- `date` 타입 → `"2026-08-28"` (`YYYY-MM-DD`)
- `datetime` 타입 → **UTC 시각인데 타임존 표기가 없다**: `"2026-09-04T14:35:02"`
- 값이 없으면 `null`

> ⚠️ **2026-09-05 정정.** 작성 당시엔 Postgres `timestamptz`라 `+00:00` 오프셋이 붙는다고 적었지만,
> MySQL 전환 후에는 naive `DATETIME`이라 오프셋 없이 직렬화된다(BE는 `session.py`에서 세션
> `time_zone='+00:00'`을 걸어 UTC로 저장한다).
>
> 이 문자열을 그대로 `new Date()`에 넣거나 `slice(0, 10)`으로 자르면 **브라우저가 로컬 시각으로
> 읽어 KST 기준 9시간이 어긋난다.** FE는 `front/src/lib/datetime.ts`의 `parseServerDate`가
> 타임존 표기가 없을 때 `Z`를 붙여 흡수한다. 서버 시각을 다룰 땐 반드시 이 헬퍼를 거친다.
>
> BE가 응답에 오프셋을 붙여주면 이 방어 코드는 필요 없어진다.

---

## 2. 헬스체크

### `GET /health`

인증 불필요. **FE 공통 client의 첫 연결 확인용.**

```json
{ "success": true, "data": { "status": "ok" } }
```

### `GET /health/db`

Supabase 연결까지 확인한다.

---

## 3. 인증 (`/auth`)

> 구현: `back/app/api/v1/auth.py` (main 머지 완료)
> 필드명은 FE 화면(`SignupPage.tsx`, `LoginPage.tsx`)에서 쓰던 이름을 그대로 쓴다: `empId`, `name`, `email`, `pw`

### 3-1. `POST /auth/verify-employee` — 사원 인증 (회원가입 1단계)

`SignupPage`의 "사원 정보 인증하기" 버튼이 호출한다.

**요청**

```json
{ "empId": "20230001", "name": "김민준" }
```

| 필드 | 타입 | 제약 |
| --- | --- | --- |
| `empId` | string | 1~20자 |
| `name` | string | 1~50자 |

**응답 (200)**

```json
{ "success": true, "data": { "verified": true } }
```

> ⚠️ **사원 명부에 없어도 200이고 `verified: false`다.** 404가 아니다. FE는 `data.verified`로 `verifyState`를 `'ok'` / `'fail'`로 정한다.

### 3-2. `POST /auth/signup` — 계정 생성 (회원가입 2단계)

**요청**

```json
{ "empId": "20230001", "name": "김민준", "email": "a@b.com", "pw": "secret123" }
```

| 필드 | 타입 | 제약 |
| --- | --- | --- |
| `empId` | string | 1~20자 |
| `name` | string | 1~50자. **1단계에서 입력한 값을 그대로 다시 보낸다** |
| `email` | string | 이메일 형식 (BE `EmailStr` 검증) |
| `pw` | string | **6자 이상 72자 이하** (bcrypt 한계) |

> BE는 FE의 1단계 통과 여부를 믿지 않고 **서버에서 사원 인증을 다시 한다.** 그래서 `name`이 필수다.
> FE는 1단계 입력값을 2단계까지 state에 들고 있어야 한다.

**응답 (200)**

```json
{ "success": true, "data": { "id": "<uuid>", "empId": "20230001", "email": "a@b.com" } }
```

**오류**

| HTTP | `code` | 상황 | FE 표시 위치 |
| :---: | --- | --- | --- |
| 400 | `EMPLOYEE_NOT_FOUND` | 사번+이름이 명부에 없음 | 사원 인증 박스 |
| 409 | `DUPLICATE_EMP_ID` | 이미 가입된 사번 | 사원 인증 박스 |
| 409 | `DUPLICATE_EMAIL` | 이미 등록된 이메일 | 이메일 입력 아래 |
| 422 | `VALIDATION_ERROR` | 형식 위반(짧은 비밀번호, 잘못된 이메일 등) | 해당 입력 아래 |

### 3-3. `POST /auth/login` — 로그인

**식별자는 이메일이 아니라 사번이다.** (`LoginPage.tsx`가 이미 사번 입력으로 되어 있음)

**요청**

```json
{ "empId": "20230001", "pw": "secret123" }
```

**응답 (200)**

```json
{ "success": true, "data": { "token": "<jwt>", "id": "<uuid>", "email": "a@b.com" } }
```

**오류**

| HTTP | `code` | 상황 |
| :---: | --- | --- |
| 401 | `INVALID_CREDENTIALS` | 사번 없음 **또는** 비밀번호 불일치 (둘을 구분하지 않는다 — 계정 존재 여부 노출 방지) |

FE 문구는 "사번 또는 비밀번호가 올바르지 않습니다." 하나로 통일한다.

### 3-4. `POST /auth/logout`

요청 본문 없음. 항상 200.

```json
{ "success": true, "data": { "message": "로그아웃되었습니다." } }
```

FE는 이 호출의 성공 여부와 무관하게 로컬 토큰을 지운다.

---

## 4. 공고 (`/announcements`)

> 구현: `back/app/api/v1/announcements.py` (`main` 머지 완료). 인증 불필요.

### 4-1. `GET /announcements` — 목록

**쿼리 파라미터**

| 이름 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `q` | string | — | 제목 부분일치 (대소문자 무시 `ilike`). **제목만 검색한다** |
| `status` | string | — | **DB 원본값과 정확히 일치**해야 함 (4-4 참고) |
| `statusLabel` | string | — | 정규화 상태 필터: `접수중` \| `접수예정` \| `마감임박` \| `마감`. 값이 다르면 400 `INVALID_STATUS_LABEL` |
| `department` | string | — | 기관/부서 완전일치 |
| `source` | string | — | `kstartup` \| `narajangteo` \| `msit` |
| `sort` | string | `latest` | `latest` \| `deadline` \| `title` |
| `page` | int | `1` | 1 이상 |
| `page_size` | int | `20` | 1~100 |

**정렬 기준**

| `sort` | DB 정렬 |
| --- | --- |
| `latest` | `reception_start DESC, id DESC` |
| `deadline` | `reception_end ASC NULLS LAST, id ASC` |
| `title` | `title ASC, id ASC` |

**응답 (200)**

```json
{
  "success": true,
  "data": [ { /* 4-3의 공고 객체 */ } ],
  "meta": { "total": 137, "page": 1, "page_size": 20 }
}
```

결과가 없으면 `data: []`, `meta.total: 0`. **오류가 아니다** — FE는 Empty UI를 띄운다.

**오류**

| HTTP | `code` | 상황 |
| :---: | --- | --- |
| 400 | `INVALID_SORT` | `sort`가 세 값 중 하나가 아님 |
| 400 | `INVALID_STATUS_LABEL` | `statusLabel`이 네 값 중 하나가 아님 |
| 422 | `VALIDATION_ERROR` | `page < 1`, `page_size > 100` 등 |

### 4-2. `GET /announcements/{id}` — 상세

`{id}`는 UUID 문자열.

**응답 (200)**: `{ "success": true, "data": { /* 4-3의 공고 객체 */ } }`

**오류**

| HTTP | `code` | 상황 |
| :---: | --- | --- |
| 404 | `ANNOUNCEMENT_NOT_FOUND` | 없는 공고 **또는 UUID 형식이 아닌 id** (형식 오류도 404로 통일) |

### 4-3. 공고 객체 (BE 응답 원형)

```json
{
  "id": "3f0c...",
  "source": "kstartup",
  "external_id": "174023",
  "title": "2026년 스마트시티 통합플랫폼 구축 사업",
  "department": "한국지능정보사회진흥원",
  "reception_start": "2026-02-05",
  "reception_end": "2026-02-28",
  "status": "Y",
  "statusLabel": "접수중",
  "detail_url": "https://...",
  "summary": "사업 개요 ...",
  "collected_at": "2026-09-04T14:35:02",
  "dday": 13
}
```

| 필드 | 타입 | null 가능 | 비고 |
| --- | --- | :---: | --- |
| `id` | string(UUID) | ✗ | |
| `source` | string | ✗ | `kstartup` \| `narajangteo` \| `msit` |
| `external_id` | string | ✗ | 출처 원본 id |
| `title` | string | ✗ | |
| `department` | string | ✓ | 수집 기관/부처 |
| `reception_start` | date | ✓ | |
| `reception_end` | date | ✓ | 마감일 |
| `status` | string | ✓ | **원본값 그대로 — 4-4 참고** |
| `statusLabel` | string | ✓ | **BE 계산 (2026-09-05 확인).** `접수중`\|`접수예정`\|`마감임박`\|`마감`. 접수 시작·마감이 둘 다 null이면 `null`. **FE도 같은 값을 자체 계산 중 — 4-4 참고** |
| `detail_url` | string | ✓ | 원문 링크 |
| `summary` | string | ✓ | |
| `collected_at` | datetime | ✗ | **UTC인데 타임존 표기가 없다** (`"2026-09-04T14:35:02"`). 1-5절 참고 |
| `dday` | int | ✓ | **BE 계산.** `reception_end - 오늘`. `reception_end`가 null이면 `null` |

### 4-4. ⚠️ `status`는 정규화되어 있지 않다 — FE가 날짜로 계산한다

**결정: FE가 `reception_start`/`reception_end`로 `StatusType`을 도출한다. BE `status` 필드는 화면 표시에 쓰지 않는다.**

이유 — `back/app/services/collector.py`가 출처마다 다른 의미의 값을 같은 컬럼에 넣고 있다:

| 출처 | 저장값 | 실제 의미 |
| --- | --- | --- |
| kstartup | `"Y"` / `"N"` (`rcrt_prgs_yn`) | 모집중 여부 |
| narajangteo | `"일반공고"` / `"재공고"` (`ntceKindNm`) | **상태가 아니라 공고 종류** |
| msit | `null` | 없음 |

단순 매핑이 불가능하고, 셋 중 하나는 애초에 상태가 아니다. 날짜 기준 도출이 세 출처 모두에 일관되게 동작하고 `dday`와도 자동으로 맞는다.

**FE 도출 규칙**

```
reception_start 가 있고 오늘 < reception_start   → '접수예정'
reception_end 가 있고 reception_end < 오늘        → '마감'
dday 가 0 이상 7 이하                              → '마감임박'
그 외 (reception_end 가 null 인 경우 포함)         → '접수중'
```

> 후속 과제: `narajangteo`의 `ntceKindNm`은 FE `announcementType`(통합공고/일반공고)에 해당한다. 다음 차수에 수집 스키마를 분리할 때 옮긴다.

**추가 (2026-08-28, BE 커밋 `50eda95`)** — BE가 같은 규칙의 `statusLabel`을 계산해 내려주기 시작했고, `?statusLabel=접수중` 필터도 생겼다(잘못된 값은 `400 INVALID_STATUS_LABEL`).
### ✅ 결정 (2026-09-05): **BE `statusLabel`이 정본이다**

FE는 더 이상 상태를 계산하지 않는다. `mapAnnouncement`가 `row.statusLabel`을 그대로 쓴다.

**이 결정 전까지 실제로 값이 어긋나 있었다.** 마감임박 기준일이 BE 3일 / FE 7일로 달랐다
(`announcements.py`의 `DEADLINE_SOON_DAYS = 3` vs `mappers.ts`의 `URGENT_DAYS = 7`).
D-5 공고로 확인한 결과 **BE `접수중` / FE 배지 `마감임박`** 으로 갈렸다. 전환으로 해소됐다.

> 참고: 대시보드의 마감임박 **건수**는 원래부터 3일 기준이었다(`DashboardPage.tsx`의 `URGENT_DAYS = 3`).
> 즉 같은 화면 안에서 배지(7일)와 건수(3일)가 서로 다른 기준을 쓰고 있었다.

**남은 예외 — 저장공고.** 저장공고 응답의 중첩 공고에는 `statusLabel`이 없어서(6절)
`mappers.ts`의 `deriveStatusFallback()`이 그 경로만 계산한다. BE 규칙과 같은 3일 기준으로 맞춰뒀다.
**BE가 저장공고 응답에도 `statusLabel`을 넣어주면 이 폴백은 삭제할 수 있다.**

**상태 필터도 서버로 이관 완료 (2026-09-05)** — `SearchPage`는 선택한 상태를 `?statusLabel=`로 넘긴다.
예전에는 화면에서 걸러서 **현재 페이지 안에서만 필터가 동작**했고, `meta.total`과 페이지 수는 필터 이전 값이라
"3건"이라 써 놓고 페이지를 넘기면 계속 나오는 상태였다. 이제 BE가 DB 전체에 필터를 걸어
`total`·페이지 수가 필터 결과와 일치한다.

> 상태 칩의 **건수는 선택된 상태에만** 표시한다. 서버 필터 결과(`total`)라 정확하지만,
> 선택하지 않은 상태의 건수는 상태별로 따로 조회하지 않는 한 알 수 없다.
> (예전에는 현재 페이지만 세서 실제 건수와 달랐다.)

**마감임박 = 3일**은 이제 FE·BE 전 경로에서 동일하다. 팀에서 공식 확정만 하면 된다
(BE 코드에는 아직 "팀 협의된 값이 아니라 임시 기준"이라는 주석이 남아 있다).

### 4-5. FE 매핑 규칙

**결정: BE 응답은 그대로 두고 FE가 매퍼 계층을 둔다.** (`front/src/lib/mappers.ts`)
BE 재작업·재머지 없이 진행할 수 있고, 응답 구조가 바뀌어도 FE 수정 지점이 한 곳이다.

| FE `Announcement` 필드 | 매핑 원본 | 비고 |
| --- | --- | --- |
| `id` | `id` | string 그대로 |
| `title` | `title` | |
| `org` | `department` | null이면 `''` |
| `department` | `department` | 현재 두 필드가 같은 값. 수집 스키마 분리 전까지 |
| `status` | `statusLabel` | **BE 값 그대로.** `null`(접수 일정 없음)이면 `'접수중'`으로 떨어뜨린다 |
| `receiptDate` | `reception_start` | null이면 `''` |
| `deadline` | `reception_end` | null이면 `''` |
| `dday` | `dday` | null이면 `0` |
| `originalUrl` | `detail_url` | |
| `originalText` | `summary` | |
| `postedDate` | `collected_at`을 **로컬 날짜로 변환** | 원문 게시일이 아니라 **수집일**. 문자열을 자르면 UTC 날짜가 나와 하루 어긋난다 — `toLocalDateString()` 사용 (1-5절) |

**BE에 대응 데이터가 없는 필드** — 이번 차수에는 값을 비운다. `types/index.ts`에서 optional(`?`)로 바꾼다.

`announcementType`, `announceType`, `field`, `deadlineTime`, `budget`, `contact`, `projectName`, `relatedKeywords`, `isFavorite`

> `isFavorite`은 공고 응답이 아니라 저장공고 API(6절) 결과로 FE가 판단한다.

---

## 5. 키워드 (`/keywords`)

> 구현: `feature/be-keywords` (**미머지 — PR 필요**)
> **모든 엔드포인트 인증 필수.** 토큰의 `sub`로 사용자를 식별한다.

### 5-1. `GET /keywords` — 내 키워드 목록

`created_at` 오름차순.

```json
{
  "success": true,
  "data": [
    { "id": "<uuid>", "keyword": "AI", "createdAt": "2026-08-28T06:00:00+00:00" }
  ]
}
```

### 5-2. `POST /keywords` — 등록

**요청**: `{ "keyword": "AI" }` (1~50자)

**응답 (200)**: `{ "success": true, "data": { "id": "<uuid>", "keyword": "AI", "createdAt": "..." } }`

**오류**

| HTTP | `code` | 상황 |
| :---: | --- | --- |
| 400 | `EMPTY_KEYWORD` | 공백 제거 후 빈 문자열 |
| 409 | `DUPLICATE_KEYWORD` | 같은 사용자가 이미 등록함 (`UNIQUE(user_id, keyword)`) |
| 401 | `UNAUTHORIZED` / `INVALID_TOKEN` | 토큰 없음 / 만료·위조 |

### 5-3. `DELETE /keywords/{id}` — 삭제

**응답 (200)**: `{ "success": true, "data": { "message": "키워드가 삭제되었습니다." } }`

**오류**

| HTTP | `code` | 상황 |
| :---: | --- | --- |
| 404 | `KEYWORD_NOT_FOUND` | 없는 키워드 **또는 다른 사용자의 키워드** (403이 아니라 404 — 소유권 노출 방지) |

### 5-4. FE 매핑 규칙

| FE `Keyword` 필드 | 매핑 원본 | 비고 |
| --- | --- | --- |
| `id` | `id` | `number` → `string`으로 타입 변경 |
| `name` | `keyword` | 이름만 다르고 같은 값 |
| `matchCount` | **없음** | 5-5 참고 |
| `dashboardAlert` | **없음** | 5-5 참고 |
| `emailAlert` | **없음** | 5-5 참고 |

### 5-5. ⚠️ `matchCount`·알림 토글은 BE에 없다 — 이번 차수는 로컬 상태로 둔다

**결정: 알림 토글(`dashboardAlert`/`emailAlert`)과 `matchCount`는 서버에 저장하지 않고 화면 상태로만 동작시킨다.** UI는 그대로 둔다.

`keywords.py` 주석대로 별도 `alert_settings` 테이블이 필요한 다음 차수 작업이다.

**초기값**: 서버에서 받은 키워드는 `matchCount: 0`, `dashboardAlert: true`, `emailAlert: false`로 채운다.

> **알려진 한계 — 시연 전에 팀이 인지할 것**
> 새로고침·재로그인하면 **키워드 목록은 유지되지만 토글 상태는 초기값으로 돌아간다.**
> 5-1plan.md 순서 14의 "새로고침·재로그인 시 데이터 유지" 점검에서 토글은 **대상에서 제외**한다.
> 시연 중 토글을 조작한 뒤 새로고침하는 동선은 피한다.

---

## 6. 저장공고 (`/saved-announcements`) — ✅ 구현 완료

BE 구현 완료(`back/app/api/v1/saved_announcements.py`, PR #9로 `main` 머지). **모두 토큰 필요.**

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `GET` | `/saved-announcements` | 내 저장공고 목록 (`saved_at` 최신순) |
| `POST` | `/saved-announcements` | `{ "announcementId": "<uuid>" }` 저장 |
| `DELETE` | `/saved-announcements/{announcementId}` | 저장 취소 (path param은 **공고 id**) |

### 6-1. 응답 형태 (`GET`·`POST` 공통)

```json
{
  "success": true,
  "data": [
    {
      "id": "저장 레코드 uuid",
      "savedAt": "2026-08-28T05:12:33.120000+00:00",
      "announcement": {
        "id": "공고 uuid",
        "title": "...",
        "department": "중소벤처기업부",
        "status": "Y",
        "receptionStart": "2026-08-01",
        "receptionEnd": "2026-09-30",
        "detailUrl": "https://..."
      }
    }
  ]
}
```

`POST`는 같은 형태의 객체 1건을 `data`로 준다. `DELETE`는 `{"success": true, "data": {"message": "저장이 취소되었습니다."}}`.

> ⚠️ **공고 목록 API와 필드 규칙이 다르다.** `/announcements`는 DB 컬럼 그대로 snake_case인데,
> 저장공고 응답의 중첩 공고는 camelCase이고 필드도 7개뿐이다(`source`·`summary`·`collected_at`·`dday` 없음).
> FE는 `lib/mappers.ts`의 `mapSavedAnnouncement`로 흡수했고, `dday`는 `receptionEnd`로 직접 계산한다
> (`computeDday` — BE `_dday`와 같은 규칙). 목록 화면이 요구하는 값은 제목·기관·마감일·상태뿐이라
> 이 응답만으로 `SavedList` 렌더에 충분하고, 상세는 어차피 `GET /announcements/{id}`로 다시 조회한다.

### 6-2. 확정된 쟁점 (구현 결과 기준)

1. `GET`은 **공고 본문을 join해서** 내려준다 — FE가 N번 상세 조회할 필요 없음. (권장안 채택)
2. `DELETE`의 path param은 **공고 id**. (권장안 채택)
3. 오류 코드는 제안(`DUPLICATE_SAVED`/`SAVED_NOT_FOUND`)과 **이름이 다르게** 구현됐다 —
   실제는 `ALREADY_SAVED`(409), `SAVED_ANNOUNCEMENT_NOT_FOUND`(404), `ANNOUNCEMENT_NOT_FOUND`(404).
   **11절 표와 FE 코드는 실제 이름을 기준으로 한다.**
4. 제약: `UNIQUE(user_id, announcement_id)`, 두 컬럼 모두 FK + `on delete cascade` (`back/app/db/models.py`의 `SavedAnnouncement`)
5. 남의 저장 데이터는 소유권을 노출하지 않도록 403이 아니라 `404 SAVED_ANNOUNCEMENT_NOT_FOUND`로 처리된다 (키워드와 동일).

> **2026-09-05 갱신** — 6주차에 Supabase(Postgres) → MySQL/MariaDB로 전환되면서 스키마 정본이
> `back/alembic/versions/`로 옮겨졌다. `back/supabase/*.sql`은 폐기됐으니 실행하지 말 것.
> 팀원 세팅은 `alembic upgrade head` 한 줄이다.
>
> 저장공고 응답의 중첩 공고에는 `statusLabel`도 없다. FE가 `receptionEnd`로 상태와 `dday`를 직접 계산한다.

---

## 7. 대시보드 (`/dashboard`) — ✅ 구현 완료

BE 구현: `back/app/api/v1/dashboard.py`. **토큰 필요.**

### 7-1. `GET /dashboard/summary`

대시보드 한 화면에 필요한 집계·목록을 한 번에 준다. 파라미터 없음.

```json
{
  "success": true,
  "data": {
    "counts": { "matched": 4, "newToday": 0, "urgent": 1, "saved": 1 },
    "matched": [ { /* 4-3의 공고 객체 */ } ],
    "saved":   [ { /* 4-3의 공고 객체 */ } ]
  }
}
```

| 필드 | 의미 |
| --- | --- |
| `counts.matched` | 내 키워드에 매칭된 공고 **총 건수** (DB 전체 기준, 아래 `matched` 배열 길이가 아니다) |
| `counts.newToday` | 그중 오늘 수집된 건수 — **⚠️ 7-3 버그 참고** |
| `counts.urgent` | 그중 `statusLabel == "마감임박"` 건수 (마감 3일 이내) |
| `counts.saved` | 내 저장공고 건수 |
| `matched` | 매칭 공고 **최신순 상위 10건** (`MATCHED_FEED_LIMIT = 10`) |
| `saved` | 내 저장공고 **전체**, `saved_at` 최신순 |

- 매칭은 **키워드별 제목 부분일치(`ILIKE`)의 OR**다. 별도 매칭 이력 테이블은 없고 조회 시점에 계산한다.
- **등록 키워드가 0개면** `matched`/`newToday`/`urgent`가 모두 `0`이고 `matched` 배열도 빈 배열이다. 저장공고만 내려온다.
- `matched`·`saved`의 원소는 목록 API와 **완전히 같은 형태**(4-3 공고 객체 + `statusLabel`)다. FE는 `mapAnnouncement`를 그대로 재사용한다.

**오류**: 토큰 없음/만료 → `401 UNAUTHORIZED` \| `401 INVALID_TOKEN`

### 7-2. FE 사용 규칙

**결정: 대시보드의 매칭·집계는 BE 값을 정본으로 쓴다.**

이전에는 FE가 `GET /announcements?page_size=100`으로 최근 100건만 받아 브라우저에서 제목을 대조했는데,
**공고가 100건을 넘는 순간 통계가 조용히 틀렸다.** 2026-09-05에 `useDashboard`(`GET /dashboard/summary`)로 교체했다.

- 화면에 표시하는 **건수**는 항상 `counts`를 쓴다. `matched` 배열은 상위 10건뿐이라 길이를 세면 안 된다.
- 마감임박 배너의 **제목**은 `matched` 안에 있는 것만 고를 수 있어 `counts.urgent`보다 적게 보일 수 있다. 건수는 `counts.urgent`가 정본이다.
- **저장공고 목록·건수는 `FavoritesContext`(`GET /saved-announcements`)를 계속 쓴다.** 별표 토글이 즉시 반영돼야 하는데 `summary`는 재조회해야만 갱신되기 때문이다.

### 7-3. ⚠️ `newToday`에 타임존 버그가 있다 (BE 수정 필요)

`dashboard.py`가 `func.date(collected_at) == date.today()`로 비교하는데,
`collected_at`은 **UTC 저장**이고 `date.today()`는 **서버 로컬(KST)**이라 9시간이 어긋난다.

2026-09-05 00:06 KST 재현 결과:

| 값 | 결과 |
| --- | --- |
| 방금 수집한 공고의 `collected_at` | `2026-09-04 15:06:46` (UTC) |
| `date(collected_at)` | `2026-09-04` |
| `date.today()` (KST) | `2026-09-05` |
| **`counts.newToday`** | **0** ← 방금 수집했는데 0건 |

**KST 00:00~08:59에 수집된 공고가 "오늘 신규"에서 전부 누락된다.** 매일 06:00 자동 수집이 바로 이 구간이라
운영에 들어가면 `newToday`가 상시 0이 될 수 있다. FE는 같은 시각을 로컬로 변환해 보므로(1-5절)
화면의 NEW 배지와 BE 집계가 서로 어긋난다. **BE에서 비교 기준을 UTC로 맞춰야 한다.**

---

## 8. 마이페이지 - 내 정보 (`/me`) — ✅ 구현 완료

BE 구현: `back/app/api/v1/me.py`. **모두 토큰 필요.**

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `GET` | `/me` | 내 정보 조회 |
| `PATCH` | `/me` | 내 정보 수정 (**이메일만**) |
| `POST` | `/me/change-password` | 비밀번호 변경 |

### 8-1. 내 정보 객체

```json
{
  "id": "fd2bb980-3474-43f9-ba9e-c4ef09343a71",
  "empId": "20230001",
  "name": "김민준",
  "department": "개발팀",
  "email": "user@example.com"
}
```

| 필드 | 타입 | null 가능 | 비고 |
| --- | --- | :---: | --- |
| `id` | string(UUID) | ✗ | `users.id` |
| `empId` | string | ✗ | 사번. **로그인 식별자라 변경 불가** |
| `name` | string | ✓ | **`employees` 테이블 소유 — 읽기 전용.** 명부에 없으면 `null` |
| `department` | string | ✓ | 위와 동일 |
| `email` | string | ✗ | **유일하게 수정 가능한 필드** |

> ⚠️ **`연락처`·`아이디`는 DB 스키마에 아예 없다.** 디자인 시안에는 있었지만 `users`/`employees`
> 어디에도 대응 컬럼이 없어서, FE `ProfileTab`은 해당 행을 표시하지 않는다.
> 필요하면 스키마 변경을 별도로 논의해야 한다.

### 8-2. `PATCH /me`

**요청**: `{ "email": "new@example.com" }` — `email` 외의 필드는 받지 않는다.
**응답**: 8-1과 같은 객체(갱신된 값).

| HTTP | `code` | 상황 |
| :---: | --- | --- |
| 409 | `DUPLICATE_EMAIL` | 다른 계정이 이미 쓰는 이메일 |
| 422 | `VALIDATION_ERROR` | 이메일 형식 오류 |

> 이메일이 기존 값과 같으면 아무것도 바꾸지 않고 현재 값을 그대로 돌려준다(오류 아님).
> `EmailStr` 검증이라 **`.test` 같은 특수용도 TLD는 거부된다(422).** 테스트 계정은 `example.com`을 쓸 것.

### 8-3. `POST /me/change-password`

**요청**: `{ "currentPw": "...", "newPw": "..." }`
**응답**: `{ "success": true, "data": { "message": "비밀번호가 변경되었습니다." } }`

| HTTP | `code` | 상황 |
| :---: | --- | --- |
| 401 | `INVALID_CREDENTIALS` | **현재 비밀번호가 틀림** |
| 422 | `VALIDATION_ERROR` | `newPw`가 6자 미만 또는 72자 초과 |

> 🔴 **401인데 토큰을 폐기하면 안 된다.** 현재 비밀번호 오답도 401이라, 401을 무조건 "토큰 만료"로
> 처리하면 **비밀번호를 잘못 입력한 사용자가 로그아웃된다.** FE 공통 client(`lib/api.ts`)는
> `UNAUTHORIZED`·`INVALID_TOKEN`일 때만 토큰을 지운다 (11절 표와 같은 규칙).

**변경 후 기존 토큰은 그대로 유효하다** — 서버가 상태를 갖지 않는 JWT라 세션이 끊기지 않는다.
재로그인은 새 비밀번호로 해야 한다.

---

## 9. 알림 (`/notifications`) — ✅ 구현 완료

BE 구현: `back/app/api/v1/notifications.py`. 데이터 원본은 `notification_logs` 테이블. **모두 토큰 필요.**

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `GET` | `/notifications` | 내 알림 목록 + 안읽음 수 |
| `POST` | `/notifications/{id}/read` | 1건 읽음 처리 |
| `POST` | `/notifications/read-all` | 전체 읽음 처리 |

### 9-1. `GET /notifications`

```json
{
  "success": true,
  "data": {
    "unreadCount": 5,
    "notifications": [
      {
        "id": "02290815-51b9-4304-b6a1-7c61c5443f3c",
        "notifyType": "신규매칭",
        "title": "[신규] AI 기반 민원 자동처리 시스템 구축",
        "keyword": "AI",
        "announcementId": "11111111-1111-4111-8111-111111111101",
        "isRead": false,
        "createdAt": "2026-09-04T14:37:40"
      }
    ]
  }
}
```

| 필드 | 타입 | null 가능 | 비고 |
| --- | --- | :---: | --- |
| `id` | string(UUID) | ✗ | 알림 id (공고 id가 아니다) |
| `notifyType` | string | ✗ | `신규매칭` \| `마감임박` |
| `title` | string | ✗ | 서버가 만든 완성 문구. FE는 가공 없이 그대로 띄운다 |
| `keyword` | string | ✓ | 매칭된 키워드. 키워드와 무관한 알림이거나 키워드가 삭제됐으면 `null` |
| `announcementId` | string(UUID) | ✓ | 클릭 시 열 공고. 공고가 삭제됐으면 `null` |
| `isRead` | boolean | ✗ | |
| `createdAt` | datetime | ✗ | **타임존 표기 없는 UTC — 1-5절 참고** |

- **최신순 최대 50건**(`LIST_LIMIT = 50`). 페이지네이션 없음.
- 알림이 없으면 `notifications: []`, `unreadCount: 0`. **오류가 아니다** — FE는 Empty UI를 띄운다.
- **"5분 전" 같은 상대 시간은 서버가 주지 않는다.** FE가 `createdAt`으로 만든다(`lib/datetime.ts`의 `formatRelativeTime`).

### 9-2. 읽음 처리

`POST /notifications/{id}/read` → `{ "message": "읽음 처리되었습니다." }`
`POST /notifications/read-all` → `{ "message": "모두 읽음 처리되었습니다.", "count": 4 }` (`count`는 이번에 처리된 건수)

| HTTP | `code` | 상황 |
| :---: | --- | --- |
| 404 | `NOTIFICATION_NOT_FOUND` | 없는 알림, **남의 알림**, 또는 UUID 형식이 아닌 id |

> 남의 알림은 403이 아니라 404다(키워드·저장공고와 동일 규칙 — 소유권 노출 방지).
> 이미 읽은 알림을 다시 읽음 처리해도 오류가 아니다(멱등).

### 9-3. FE 사용 규칙

- 배지(안읽음 수)와 드롭다운 목록이 같은 데이터를 봐야 해서 `Header`에서 `useNotifications()`를 한 번만 부르고 `AlertsDropdown`에 props로 내린다.
- 읽음 처리는 **낙관적 갱신** 후 실패 시 서버 상태로 되돌린다.
- 드롭다운을 열 때마다 재조회한다.

### 9-4. 알림을 "쌓는" 파이프라인 — 연결되어 있다

이 API 자체는 `notification_logs`를 **조회·읽음 처리**만 하지만,
알림을 생성하는 파이프라인은 이미 스케줄러에 연결돼 있다 (`back/app/core/scheduler.py`의 `run_daily_collect`):

```
매일 06:00 (COLLECT_CRON_HOUR/MINUTE)
  → collect_all()                             공공데이터포털 3종 수집
  → save_announcements()                      announcements upsert
  → generate_keyword_match_notifications()    키워드 매칭 → notification_logs 생성
  → send_pending_notification_emails()        미발송 알림 이메일 발송
```

> **2026-09-05 정정.** 진행상황 문서에는 "06:00 수집 이후 단계 없음 / 알림·이메일 발송 미구현"으로
> 적혀 있으나, 위 4단계는 이미 코드에 연결돼 있다. `generate_keyword_match_notifications()`를
> 직접 호출해 알림 5건(신규매칭 4 + 마감임박 1)이 생성되는 것도 확인했다.

**동작 전제 2가지** — 둘 다 `back/.env` 설정 문제이지 미구현이 아니다.

| 값 | 없으면 |
| --- | --- |
| `DATA_GO_KR_API_KEY` | 수집 자체가 안 되므로 새 공고가 없고 → 알림도 안 쌓인다 |
| `SMTP_*` | 알림은 `notification_logs`에 정상 저장되고 **이메일만 안 나간다** (의도된 동작) |

따라서 **알림 목록이 비어 있다면 대개 수집 API 키 미설정이 원인**이다. 알림 API의 버그가 아니다.

---

## 10. 관리자 (`/admin`) — ✅ 구현 완료

BE 구현: `back/app/api/v1/admin.py`. **모두 토큰 필요 + `users.is_admin = true`.** 비관리자는 `403`.
로그인 응답의 `isAdmin`으로 FE가 진입을 막는다.

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `GET` | `/admin/employees` | 사원 명부 목록 |
| `POST` | `/admin/employees` | 사원 명부 등록 |
| `DELETE` | `/admin/employees/{empId}` | 사원 명부 삭제 (**미가입 사원만**) |
| `GET` | `/admin/users` | 가입자(계정) 목록 |
| `DELETE` | `/admin/users/{userId}` | 가입자 삭제 (= 접근 차단) |

> 계정(`users`)은 본인이 이메일·비밀번호를 정하는 회원가입 절차로만 생성된다.
> **관리자가 직접 만들 수 있는 건 사원 명부(`employees`)뿐이고**, 그 사번으로 본인이 가입하는 흐름이다.

### 10-1. 사원 객체 / 가입자 객체

```json
// employees
{ "empId": "20230001", "name": "김민준", "department": "개발팀",
  "createdAt": "2026-09-04T14:35:02", "joined": true }

// users
{ "id": "<uuid>", "empId": "20230001", "name": "김민준", "department": "개발팀",
  "email": "user@example.com", "isAdmin": false, "createdAt": "2026-09-04T14:36:00" }
```

- `joined` — 그 사번으로 **이미 가입한 계정이 있는지**. `true`면 명부에서 삭제할 수 없다.
- 두 목록 모두 `createdAt` 최신순. 페이지네이션 없음.
- `POST /admin/employees` 요청: `{ "empId", "name", "department" }` (`department`는 선택, `null` 허용).

### 10-2. 오류

| HTTP | `code` | 상황 |
| :---: | --- | --- |
| 403 | `FORBIDDEN` | 관리자가 아님 |
| 409 | `DUPLICATE_EMP_ID` | 이미 등록된 사번 |
| 404 | `EMPLOYEE_NOT_FOUND` | 없는 사원 |
| 409 | `EMPLOYEE_ALREADY_JOINED` | **이미 가입한 사원은 명부에서 삭제 불가** — 계정을 먼저 지워야 한다 |
| 404 | `USER_NOT_FOUND` | 없는 가입자 또는 UUID 형식이 아닌 id |

> 이 브랜치(`feature/fe-api-integration`)에는 관리자 화면이 없다. `main`의 `AdminPage`·`RequireAdmin`이
> 통합될 때 이 절을 기준으로 맞춘다.

---

## 11. 오류 코드 전체 목록

FE는 이 표를 기준으로 화면 문구를 고른다. 표에 없는 `code`는 `error.message`를 그대로 띄운다.

| `code` | HTTP | 발생 위치 | FE 처리 |
| --- | :---: | --- | --- |
| `EMPLOYEE_NOT_FOUND` | 400 | signup | 사원 인증 박스에 오류 표시 |
| `DUPLICATE_EMP_ID` | 409 | signup | 사원 인증 박스에 오류 표시 |
| `DUPLICATE_EMAIL` | 409 | signup | 이메일 입력 아래 오류 표시 |
| `INVALID_CREDENTIALS` | 401 | login | 로그인 폼 아래 오류 표시. **토큰 폐기 로직을 타지 않게 예외 처리** |
| `UNAUTHORIZED` | 401 | 인증 필요 API | 토큰 폐기 → 로그인 화면 |
| `INVALID_TOKEN` | 401 | 인증 필요 API | 토큰 폐기 → 로그인 화면 |
| `INVALID_SORT` | 400 | 공고 목록 | 개발 중 실수. 기본 정렬로 복구 |
| `ANNOUNCEMENT_NOT_FOUND` | 404 | 공고 상세 | "삭제되었거나 존재하지 않는 공고입니다" |
| `EMPTY_KEYWORD` | 400 | 키워드 등록 | 입력 아래 오류 표시 |
| `DUPLICATE_KEYWORD` | 409 | 키워드 등록 | "이미 등록된 키워드입니다" |
| `KEYWORD_NOT_FOUND` | 404 | 키워드 삭제 | 목록 재조회 |
| `ALREADY_SAVED` | 409 | 저장공고 저장 | 이미 저장된 상태 — 저장공고 목록 재조회로 화면을 DB에 맞춤 |
| `SAVED_ANNOUNCEMENT_NOT_FOUND` | 404 | 저장공고 취소 | 이미 취소된 상태 — 저장공고 목록 재조회 |
| `INVALID_STATUS_LABEL` | 400 | 공고 목록 | 개발 중 실수. 필터 없이 재조회 |
| `DUPLICATE_EMAIL` | 409 | **`PATCH /me`** | 이메일 입력 아래 오류 표시 |
| `INVALID_CREDENTIALS` | 401 | **`POST /me/change-password`** | 현재 비밀번호 입력 아래 오류 표시. **토큰 폐기 금지** |
| `NOTIFICATION_NOT_FOUND` | 404 | 알림 읽음 처리 | 이미 지워진 알림 — 알림 목록 재조회 |
| `FORBIDDEN` | 403 | 관리자 API | 관리자 화면 진입 차단 (로그인 상태는 유지) |
| `EMPLOYEE_ALREADY_JOINED` | 409 | 사원 명부 삭제 | "이미 가입한 사원입니다" — 계정을 먼저 삭제하도록 안내 |
| `USER_NOT_FOUND` | 404 | 가입자 삭제 | 목록 재조회 |
| `VALIDATION_ERROR` | 422 | 전역 | 해당 입력 아래 오류 표시 |
| `HTTP_ERROR` | 4xx | 전역(라우팅 404 등) | 공통 Error UI |
| `INTERNAL_ERROR` | 500 | 전역 | 공통 Error UI + 재시도 버튼 |

> ⚠️ `INVALID_CREDENTIALS`도 401이다. **401을 무조건 "토큰 만료"로 처리하면 잘못 동작한다** —
> 로그인 실패뿐 아니라 **비밀번호 변경 시 현재 비밀번호 오답(8-3절)에도 사용자가 로그아웃된다.**
> FE 공통 client(`lib/api.ts`)는 `UNAUTHORIZED`·`INVALID_TOKEN`일 때만 토큰을 폐기한다.

---

## 12. 순서 1 확정 결과 요약

| # | 항목 | 결정 |
| :---: | --- | --- |
| 1 | 공고 필드명 | **FE 매퍼 계층** (`lib/mappers.ts`). BE 응답 변경 없음 |
| 2 | BE에 없는 공고 필드 | `types/index.ts`에서 optional 처리, 이번 차수 공백 |
| 3 | 공고 `status` | **FE가 날짜로 도출.** BE `status`는 화면에 쓰지 않음 |
| 4 | 키워드 알림·matchCount | **로컬 상태로만 동작.** 새로고침 시 초기화되는 한계 인지 |
| 5 | signup 요청 | `name` 포함 4개 필드. 서버가 사원 인증 재검증 |
| 6 | 비밀번호 | 6~72자. FE도 동일 검증 |
| 7 | 로그인 식별자 | `empId` (사번). FE 이미 사번 입력 — 변경 불필요 |
| 8 | 오류 코드 | 11절 표로 확정 |
| 9 | 날짜 | `date`는 `YYYY-MM-DD`, `datetime`은 ISO8601+UTC 오프셋 |
| 10 | id 타입 | **모두 string(UUID).** FE 타입 수정 필요 |

**남은 BE 작업**: 없음 (미머지 브랜치 2개·저장공고 API 모두 `main` 머지 완료). 단, `saved_announcements` 테이블 생성 SQL 실행과 `announcements` 실데이터 적재는 남아 있다.

---

## 13. 2026-09-05 갱신 요약

### 13-1. 계약서에 새로 들어온 것

| 절 | 영역 | 상태 |
| :---: | --- | --- |
| 7 | 대시보드 `/dashboard/summary` | ✅ BE 구현 완료, FE 연동 완료 |
| 8 | 마이페이지 `/me` (조회·이메일 수정·비밀번호 변경) | ✅ BE 구현 완료, FE 연동 완료 |
| 9 | 알림 `/notifications` (목록·읽음·모두읽음) | ✅ BE 구현 완료, FE 연동 완료 |
| 10 | 관리자 `/admin` (사원 명부·가입자) | ✅ BE 구현 완료, **이 브랜치엔 FE 화면 없음** |

### 13-2. 정정된 기존 서술

| 절 | 무엇이 틀렸었나 |
| :---: | --- |
| 1-5 | `datetime`에 UTC 오프셋이 붙는다고 적혀 있었으나, **MySQL 전환 후 오프셋이 없다.** 그대로 파싱하면 9시간 어긋남 |
| 4-1 / 4-3 | `statusLabel` 쿼리 파라미터와 응답 필드가 누락돼 있었음 |
| 4-4 | 마감임박 기준이 "BE 3일 / FE 7일 불일치"로 적혀 있었으나 **현재는 양쪽 다 3일** |
| 4-5 | `postedDate`를 `collected_at` 문자열 자르기로 만든다고 적혀 있었으나, **로컬 날짜 변환이 필요** |
| 6 | Supabase SQL 파일을 실행하라고 안내했으나, **폐기됨.** 스키마 정본은 alembic |

### 13-3. 남은 결정·작업

| 구분 | 내용 |
| --- | --- |
| ✅ 결정됨 | `statusLabel` **정본 = BE**. FE `deriveStatus` 제거 (4-4절) |
| 🔶 팀 결정 | "마감임박 = 3일" 공식 확정 (전환 후 전 경로 일치) |
| 🔵 BE 요청 | 저장공고 응답에도 `statusLabel` 추가 → FE 폴백 계산 완전 제거 가능 (4-4절) |
| ✅ 완료 | 검색 상태 필터를 `?statusLabel=` 서버 쿼리로 이관 (4-4절) |
| 🔴 BE 수정 | `dashboard/summary`의 `newToday` 타임존 버그 (7-3절) |
| ⬜ BE 미구현 | `alert_settings` — 마이페이지 알림 설정 탭이 이것 때문에 연동 불가 |
| ⚙️ 설정 필요 | `06:00 수집 → 매칭 → 알림 생성 → 이메일 발송` 파이프라인은 **이미 연결됨**. `DATA_GO_KR_API_KEY`(수집)와 `SMTP_*`(이메일) 설정만 남음 (9-4절) |

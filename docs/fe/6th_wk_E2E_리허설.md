# 6주차 E2E 리허설 결과

> 진행상황 md의 FE P0 항목 "E2E 통합 점검"에 대한 실행 기록
> 실행일: 2026-09-04 (BE 수정 재검증: 2026-09-05) / 실행자: FE

## 1. 실행 환경

깃 브랜치 통합이 보류 상태(BE 담당자 작업 중)라, 저장소와 브랜치를 건드리지 않고 아래 조합으로 리허설했습니다.

| 구성 | 내용 |
|---|---|
| FE | `feature/fe-api-integration` 워킹트리, Vite dev `http://localhost:8443` |
| BE | `origin/main` 코드를 `git archive`로 임시 폴더에 복사해 기동, uvicorn `http://127.0.0.1:8000` |
| DB | 로컬 MySQL 8.0, `forward` 스키마. `alembic upgrade head`로 4개 리비전 적용 (`0001` → `0002` → `dfe33474e50a` → `822df0e14869`) |
| 데이터 | `DATA_GO_KR_API_KEY` 미보유로 실제 수집 불가 → 사원 1명 + 공고 5건 수동 시드 |

> ⚠️ 워킹트리의 `back/`은 아직 Supabase(Postgres) 시절 코드라(라우터에 `keywords`/`dashboard`/`me`/`notifications` 없음) 그대로는 리허설이 불가능합니다.
> FE는 이 브랜치, BE는 main인 **혼합 조합**이므로, 브랜치 통합 후 main 기준으로 한 번 더 리허설이 필요합니다.

## 2. 리허설 결과 — 22개 항목 전부 통과

md가 요구한 흐름 `로그인 → 대시보드 → 검색 → 상세 → 저장 → 키워드`에 정상 경로와 실패 경로를 함께 넣어 확인했습니다.

| # | 단계 | 요청 | 결과 |
|:--:|---|---|---|
| 1 | 사원 인증 | `POST /auth/verify-employee` (명부 O) | ✅ `verified: true` |
| 2 | 사원 인증 | `POST /auth/verify-employee` (명부 X) | ✅ `verified: false` — 오류가 아니라 false로 응답 |
| 3 | 회원가입 | `POST /auth/signup` | ✅ 201 상당, `id/empId/email` 반환 |
| 4 | 회원가입 | 같은 사번 재가입 | ✅ 409 `DUPLICATE_EMP_ID` |
| 5 | 로그인 | 틀린 비밀번호 | ✅ 401 `INVALID_CREDENTIALS` |
| 6 | 로그인 | 정상 | ✅ `token/id/email/name/isAdmin` 반환 |
| 7 | 인증 가드 | 토큰 없이 `GET /dashboard/summary` | ✅ 401 `UNAUTHORIZED` |
| 8 | 인증 가드 | 위조 토큰으로 `GET /me` | ✅ 401 `INVALID_TOKEN` |
| 9 | 대시보드 | `GET /dashboard/summary` (키워드 등록 전) | ✅ 전 항목 0 |
| 10 | 검색 | `GET /announcements?q=AI` | ✅ 2건, `meta.total=2`, `statusLabel`·`dday` 포함 |
| 11 | 상세 | `GET /announcements/{id}` | ✅ 단건 반환 |
| 12 | 상세 | 없는 id | ✅ 404 `ANNOUNCEMENT_NOT_FOUND` |
| 13 | 저장 | `POST /saved-announcements` | ✅ 저장 레코드 + 중첩 공고 반환 |
| 14 | 저장 | 같은 공고 재저장 | ✅ 409 `ALREADY_SAVED` |
| 15 | 저장 | `GET /saved-announcements` | ✅ 1건 |
| 16 | 키워드 | `POST /keywords` × 2 (`AI`, `데이터`) | ✅ 등록 |
| 17 | 키워드 | 같은 키워드 재등록 | ✅ 409 `DUPLICATE_KEYWORD` |
| 18 | 대시보드 | 키워드 등록 후 재조회 | ✅ `matched 4 / newToday 4 / urgent 1 / saved 1` — 실시간 매칭 동작 확인 |
| 19 | 내 정보 | `GET /me` | ✅ `empId/name/department/email` |
| 20 | 내 정보 | `PATCH /me` 이메일 변경 / 잘못된 형식 | ✅ 변경됨 / 422 `VALIDATION_ERROR` |
| 21 | 비밀번호 | `POST /me/change-password` 오답 / 정상 → 새 비번 재로그인 | ✅ 401 `INVALID_CREDENTIALS` / 변경 후 재로그인 성공 |
| 22 | 알림 | `GET /notifications` → 1건 읽음 → `read-all` | ✅ `unreadCount 5 → 4 → 0`, 없는 id는 404 `NOTIFICATION_NOT_FOUND` |
| 23 | 저장 취소 | `DELETE /saved-announcements/{공고id}` | ✅ 목록 0건 |

알림 데이터는 `services/notifier.py`의 `generate_keyword_match_notifications()`를 직접 호출해 5건 생성했습니다(신규매칭 4 + 마감임박 1). 06:00 스케줄러 파이프라인 자체는 이번 리허설 범위 밖입니다.

## 3. 발견 이슈

### 3.1 [P0/BE·해결됨] main의 `router.py`가 기동 불가 — 서버가 뜨지 않음

> **2026-09-05 재검증: 해결 확인.** PR #22(`c1ecfce`)로 수정됨. main 코드를 임시 패치 없이 그대로 받아
> 재기동한 결과 정상 기동, 라우팅 경로 23개에 `/me`·`/notifications` 5개 전부 등록됨.
> `GET /me`, `GET /notifications`, `POST /notifications/read-all`, `GET /dashboard/summary` 실호출도 모두 정상.

아래는 최초 발견 당시 기록입니다.


`back/app/api/v1/router.py`에서

- `me`를 import하지 않은 채 `include_router(me.router)` 호출 → **`NameError`로 서버 기동 실패**
- `notifications`는 import만 되고 `include_router`가 누락 → 알림 API 3종이 라우팅되지 않음

PR #19/#21 머지 과정에서 생긴 것으로 보입니다. 리허설은 임시 복사본에서 아래처럼 고쳐 진행했습니다.

```python
from app.api.v1 import admin, announcements, auth, collect, dashboard, health, keywords, me
...
api_router.include_router(me.router)
api_router.include_router(notifications.router)
```

→ PR #22로 수정 완료 (위 재검증 참고).

### 3.2 [P1/FE·해결됨] 서버 시각이 타임존 표기 없는 UTC — 날짜/시간이 9시간 어긋남

BE는 DB에 UTC로 저장하고(`session.py`의 `time_zone='+00:00'`), FastAPI는 naive datetime을 `"2026-09-04T14:37:40"`처럼 **타임존 표기 없이** 직렬화합니다. 이를 그대로 `new Date()`에 넣거나 문자열을 자르면 KST 기준 9시간이 어긋납니다.

- 실제 영향: `mappers.ts`가 `collected_at.slice(0, 10)`으로 `postedDate`를 만들고 대시보드가 이를 로컬 날짜와 비교 → **KST 00:00~08:59 사이에 "오늘 신규"가 항상 0건**
- 조치: `front/src/lib/datetime.ts` 신설(`parseServerDate` / `toLocalDateString` / `formatRelativeTime`). `mappers.ts`의 `postedDate`를 로컬 날짜 변환으로 교체하고, 알림 드롭다운의 상대 시간도 같은 헬퍼를 사용.
- BE 측 권장: 응답에 `Z`(또는 오프셋)를 붙여주면 FE 방어 코드가 불필요해집니다.

### 3.3 [P1/BE] `dashboard/summary`의 `newToday`에도 같은 타임존 버그 — **재현 확인됨**

`dashboard.py`가 `func.date(Announcement.collected_at) == date.today()`로 비교합니다.
`collected_at`은 UTC 저장인데 `date.today()`는 서버 로컬(KST)이라 9시간이 어긋납니다.

2026-09-05 00:06 KST에 재현 실험한 결과:

| 값 | 결과 |
|---|---|
| 방금 수집한 공고의 `collected_at` | `2026-09-04 15:06:46` (UTC) |
| `date(collected_at)` | `2026-09-04` |
| `curdate()` / `date.today()` (KST) | `2026-09-05` |
| **BE `counts.newToday`** | **0** ← 방금 수집했는데 0건 |

즉 **KST 00:00~08:59에 수집된 공고는 "오늘 신규"에서 전부 누락**됩니다. 매일 06:00 수집이 바로 이 구간이라
정상 운영 시 `newToday`가 상시 0이 될 수 있습니다.

FE는 같은 시각을 로컬로 변환해 보기 때문에(3.2 조치) 화면의 NEW 배지와 BE 집계가 서로 어긋나게 됩니다.
BE에서 비교 기준을 UTC로 맞추거나(`utcnow().date()`), `collected_at`을 KST로 변환해 비교해야 합니다.

### 3.4 [정보] 마감 임박 기준 = 3일로 FE·BE 일치

md의 P0 "마감 임박 기준 확정" 관련. BE `announcements.py:45`의 `DEADLINE_SOON_DAYS = 3`에는
"팀 협의된 값이 아니라 임시 기준"이라는 주석이 붙어 있습니다. 시드 공고 중 D-2 1건에 대해 BE `dashboard/summary`의 `urgent`가 1을 반환했고, FE `DashboardPage.tsx`의 `URGENT_DAYS`도 3입니다. **양쪽이 이미 3일로 일치**하므로 이 값을 공식 기준으로 확정하면 됩니다. 단 `AlertsTab`의 마감임박 기준일 선택(D-7/3/1)은 저장되지 않으므로 별개 사안입니다.

### 3.5 [주의] `.test` TLD 이메일은 가입 불가

`EmailStr`이 `user@example.test`를 거부합니다(422). 제품 버그는 아니고 테스트 데이터 작성 시 주의할 점입니다 — 테스트 계정은 `example.com`을 쓰세요.

## 4. 남은 범위

| 항목 | 상태 |
|---|---|
| UI 레벨 리허설(실제 브라우저 클릭 흐름) | ⬜ 미실행 — 브라우저 확장 미연결. API 레벨로 대체함 |
| main 통합 후 재리허설 | ⬜ FE/BE 브랜치 통합 이후 필요 |
| 06:00 수집 → 매칭 → 알림 생성 → 이메일 발송 파이프라인 | ⚙️ **코드는 이미 연결돼 있음** (`core/scheduler.py`의 `run_daily_collect`). `DATA_GO_KR_API_KEY`·`SMTP_*` 설정 후 실제 실행 검증 필요 |
| 마이페이지 알림 설정(`AlertsTab`) | ⬜ `alert_settings` API 부재로 연동 불가 |

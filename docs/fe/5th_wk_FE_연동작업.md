# 5주차 FE 연동 작업 순서 (BE API 완료 기준)

> `docs/be/5th_wk/5-1plan.md` 기준으로 BE가 먼저 완성한 4개 기능(회원가입/로그인, 공고 검색·필터·정렬·페이지네이션·상세조회, 키워드 CRUD, 저장공고 CRUD)을
> FE에 연동하기 위한 작업 순서입니다. 화면(JSX)은 대부분 이미 만들어져 있으므로, 원칙적으로 **mock 데이터를 참조하던 부분만 실제 API 호출로 교체**합니다.

## 0. 시작 전 참고

- 리뷰 중 `back/app/api/v1/keywords.py`가 실제로는 라우터에 등록돼 있지 않고(`router.py`), `models.py`에 `Keyword` 모델도 빠져 있던 버그를 발견해 고쳐놨습니다(머지 충돌 해결 과정에서 유실됨). 이제 `GET/POST/DELETE /api/v1/keywords`는 정상 동작합니다.
- 아래 BE 응답 형식은 실제 코드(`back/app/api/v1/*.py`)를 읽고 정리한 것이며, 성공 응답은 전부 `{"success": true, "data": ...}` (목록은 `meta`에 페이지 정보 추가), 오류는 `{"success": false, "error": {"code","message"}}` 형식입니다.

---

## 1. 먼저 맞춰야 할 FE·BE 계약 불일치

코드를 뜯어보면 5-1plan.md가 미리 경고한 것 외에 다음 불일치가 실제로 있습니다. 연동 전에 먼저 결정하고 시작하세요.

| 항목 | FE 현재 (`types/index.ts` 등) | BE 실제 응답 | 필요한 조치 |
| --- | --- | --- | --- |
| id 타입 | `Announcement.id`, `Keyword.id` = `number` | UUID 문자열 | 둘 다 `string`으로 변경 (5-1plan에서 이미 예고됨) |
| 키워드 필드명 | `Keyword.name` | `{id, keyword, createdAt}` | FE 필드명을 `keyword`로 맞추거나 매핑 함수 작성 |
| 키워드 부가기능 | `matchCount`, `dashboardAlert`, `emailAlert` | 없음 (`id`, `keyword`, `createdAt`만 반환) | 이번 범위에서 구현 불가 — UI에서 숨기거나 더미 표시. `alert_settings` 테이블은 다음 작업(BE 우선순위 P1) |
| 공고 필드 | `org`, `announcementType`, `announceType`, `field`, `postedDate`, `receiptDate`, `deadlineTime`, `budget`, `contact`, `projectName`, `originalText`, `relatedKeywords` | `source`, `external_id`, `title`, `department`, `reception_start`, `reception_end`, `status`, `statusLabel`, `detail_url`, `summary`, `collected_at`, `dday` | FE 필드 상당수가 BE에 없음. 화면에서 실제로 쓰는 필드만 남기고 나머지는 제거하거나 BE에 추가 요청 (`relatedKeywords`는 BE에 없으므로 키워드 매칭 하이라이트는 이번엔 불가) |
| 로그인 응답 | — | `{token, id, email}` (empId 없음) | 헤더 등에 사번 표시가 필요하면 로그인 시 별도 저장(입력값 재사용) 또는 BE에 empId 추가 요청 |
| 인증 방식 | `sessionStorage` 플래그(`lib/auth.ts`) | `Authorization: Bearer <JWT>` | `lib/auth.ts` 전면 재작성 필요 |

---

## 2. 작업 순서

### 순서 1 — 공통 API Client 신설 (`front/src/lib/api.ts`)

- `import.meta.env.VITE_API_BASE_URL`로 base URL 분리 (`.env`에 `VITE_API_BASE_URL=http://localhost:8000/api/v1` 등 추가)
- fetch 기반 공통 요청 함수: JSON 파싱, `{success:false, error}` 형식이면 에러로 throw
- `sessionStorage`(또는 결정한 저장소)에서 토큰을 읽어 `Authorization: Bearer <token>` 자동 첨부
- 401 응답 시 저장된 토큰 제거 + 로그인 페이지로 리다이렉트 처리 훅
- 완료 기준: `GET /api/v1/health` 호출 성공

### 순서 2 — 회원가입 연동 (`SignupPage.tsx`)

- `handleVerify` 내부 `setTimeout` + 하드코딩(`20230001`/`김민준`) 제거 → `POST /auth/verify-employee { empId, name }` 호출, 응답 `data.verified`로 `verifyState` 결정
- 가입 버튼 → `POST /auth/signup { empId, name, email, pw }`
- 오류 코드별 메시지 표시: `EMPLOYEE_NOT_FOUND`(사원 인증 실패), `DUPLICATE_EMP_ID`, `DUPLICATE_EMAIL`
- 제출 버튼 중복 클릭 방지(로딩 상태)
- 성공 시 기존과 동일하게 `/signup/done`으로 이동

### 순서 3 — 로그인·인증 상태 연동 (`LoginPage.tsx`, `lib/auth.ts`, `RequireAuth.tsx`)

- `lib/auth.ts`를 토큰 기반으로 재작성: `login(token)`이 토큰을 저장, `isAuthenticated()`는 토큰 존재(+ 필요하면 만료 여부)로 판단, `logout()`은 토큰 제거
- `LoginPage.tsx`의 `onLogin`을 `POST /auth/login { empId, pw }` 호출로 교체, 성공 시 `data.token` 저장 후 이동
- 실패 시(`INVALID_CREDENTIALS`) 에러 메시지 표시
- `RequireAuth.tsx`는 `isAuthenticated()` 구현만 바뀌면 그대로 동작
- 로그아웃 버튼은 `POST /auth/logout` 호출(서버는 상태가 없어 실질적으로는 로컬 토큰 삭제가 핵심) 후 토큰 제거

### 순서 4 — 공고 목록·검색·상세 연동

대상 파일: `types/index.ts`, `SearchPage.tsx`, `ResultsTable.tsx`, `Pagination.tsx`, `DetailModal.tsx`, `data/mock/announcements.ts` 제거

- `Announcement` 타입을 BE 응답 기준으로 재정의 (`id: string`, `title`, `department`, `status`, `statusLabel`, `reception_start`, `reception_end`, `detail_url`, `summary`, `dday` 등). 화면에서 실제로 못 쓰는 필드(`org`, `field`, `budget` 등)는 걷어내거나 표시 문구를 바꿔야 함
- `SearchPage.tsx`의 `useMemo` 클라이언트 필터링 제거 → `GET /announcements?q=&statusLabel=&sort=&page=&page_size=` 호출로 대체 (검색어 입력, 상태 필터 버튼, 페이지 변경마다 재요청)
  - 상태 필터는 FE의 `StatusType`(접수중/접수예정/마감임박/마감)을 그대로 `statusLabel` 파라미터로 보내면 됨
- `Pagination.tsx`는 이미 `currentPage/totalPages/onChange` 형태라 그대로 재사용 가능, `totalPages`만 응답의 `meta.total`/`meta.page_size`로 계산
- `DetailModal.tsx`는 mock 배열에서 `find`하던 부분을 제거하고, 목록에서 클릭 시 이미 갖고 있는 행 데이터를 그대로 넘기거나 `GET /announcements/{id}`를 다시 호출 (404 시 "존재하지 않는 공고" 처리)
- Loading / Empty(검색 결과 0건) / Error(네트워크·서버 오류) 상태 UI 추가

### 순서 5 — 키워드 연동 (`useKeywords.ts`, `KeywordsTab.tsx`)

- `useKeywords` 내부 구현만 교체 (Context나 `KeywordsTab.tsx` JSX는 그대로 두되, `kw.name` 참조는 `kw.keyword`로 수정 필요)
- 초기 로드: `GET /keywords` → `data` 배열로 상태 채우기 (`INITIAL_KEYWORDS` mock 제거)
- `addKeyword`: `POST /keywords { keyword }`, 성공 시 서버 응답으로 목록 갱신. 빈 값(`EMPTY_KEYWORD`)·중복(`DUPLICATE_KEYWORD`) 오류 메시지 표시
- `removeKeyword`: `DELETE /keywords/{id}`, 404(`KEYWORD_NOT_FOUND`) 처리
- `matchCount`/`dashboardAlert`/`emailAlert`는 BE 미구현이므로 UI에서 숨기거나(추천) "준비 중" 처리 — 억지로 값을 만들어내지 말 것
- 모든 요청은 인증 필요 (순서 1의 API client가 토큰을 자동 첨부하는지 확인)

### 순서 6 — 저장공고 연동 (`useFavorites.ts`, `DetailModal.tsx`, `ResultsTable.tsx`, `SavedList.tsx`)

- `useFavorites` 내부 구현만 교체: `favorites: Set<number>` → `Set<string>`
- 초기 로드: `GET /saved-announcements` → 응답의 `data[].announcement.id`로 Set 채우기 (`ANNOUNCEMENTS.filter(isFavorite)` mock 제거)
- `toggleFavorite(id)`: 저장 안 된 상태면 `POST /saved-announcements { announcementId: id }`, 이미 저장된 상태면 `DELETE /saved-announcements/{id}`
  - 5-1plan 원칙대로 **응답 성공 후에 화면 상태 확정** (낙관적 업데이트로 먼저 바꾸지 않기)
  - 중복 저장(`ALREADY_SAVED`) 오류는 이미 저장된 것으로 간주하고 무시해도 됨
- `SavedList.tsx`가 쓰는 공고 정보는 저장공고 응답에 포함된 `announcement` 객체(`title`, `department`, `status`, `receptionStart`, `receptionEnd`, `detailUrl`)만 사용 가능 — 전체 `Announcement` 타입과 필드가 다르니 별도 타입 필요할 수 있음

---

## 3. 이번 BE 범위에 없어서 FE도 보류해야 하는 것

- **대시보드 집계** (`DashboardPage.tsx`, `StatsGrid.tsx`, `MatchedFeed.tsx`) — 오늘 신규/매칭/마감임박 집계 API가 아직 없음(BE 우선순위 문서 기준 별도 작업). 계속 mock 유지
- **키워드 매칭 개수**(`matchCount`), **알림 on/off**(`dashboardAlert`/`emailAlert`) — `alert_settings` 테이블/API 미구현
- **마이페이지 내정보 수정, 알림 설정, 이메일 발송** — 전부 BE P1 항목으로 아직 없음

---

## 4. 연동 완료 체크리스트 (이번에 만든 4개 기능 한정)

- [ ] `lib/api.ts` 공통 client 생성, `/api/v1/health` 호출 성공
- [ ] `types/index.ts`의 `Announcement.id`/`Keyword.id`가 `string`
- [ ] 사원 명부에 없는 사번·이름은 인증 단계에서 걸러짐 (`verify-employee` 연동)
- [ ] 회원가입 성공 시 Supabase `users`에 실제로 저장됨, 중복 사번·이메일 차단 확인
- [ ] `lib/auth.ts`가 JWT 기반으로 동작, 로그인 실패·만료 메시지 표시
- [ ] `data/mock/announcements.ts` 제거, 검색·상태필터·정렬·페이지 이동이 실제 API와 연결
- [ ] 공고 상세 모달이 실제 데이터로 열리고, 존재하지 않는 id는 404 처리됨
- [ ] `useKeywords`가 mock 없이 API로 동작 (`kw.keyword` 필드명 반영), 새로고침 후 유지
- [ ] `useFavorites`가 mock 없이 API로 동작, 저장/취소가 Supabase와 일치, 새로고침 후 유지
- [ ] 미인증 상태로 키워드/저장공고 API 호출 시 401 → 로그인 페이지로 이동 확인

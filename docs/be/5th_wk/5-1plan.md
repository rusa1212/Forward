# 5주차-1차 FE·BE 개발 참고

## 0. 현재 상태 요약 (수정 전 계획서와의 차이)

이 계획서는 처음에 "아무것도 없는 상태"를 가정하고 작성됐지만, 실제로는 아래처럼 이미 진행된 부분과 결정되지 않은 부분이 섞여 있다. 작업 전에 반드시 확인한다.

**이미 되어 있는 것**

- BE: `back/app/main.py`에 FastAPI 앱과 CORS 미들웨어가 이미 구성되어 있고, `back/app/api/v1/router.py`가 `/api/v1` prefix로 라우터를 묶는다.
- BE: `GET /api/v1/health`, `GET /api/v1/health/db`, `GET /api/v1/announcements`(목록만, 검색·정렬·페이지네이션 없음)가 이미 동작한다.
- BE: 성공 응답은 이미 `{"success": true, "data": ...}` 형태로 통일되어 있다 (`health.py`, `announcements.py` 참고). **새 API도 이 포맷을 그대로 따른다.**
- BE: SQLAlchemy 모델은 `back/app/db/models.py`에 있고, Supabase에 이미 만들어진 테이블과 1:1로 대응시키는 방식이다. 지금은 `Announcement` 모델 하나뿐이다.
- FE: 로그인/회원가입/대시보드/검색/마이페이지 화면(`front/src/pages/**`)이 이미 UI로 완성되어 있고, `front/src/data/mock/*.ts` 목데이터로 동작 중이다.
- FE: `KeywordsContext`(`useKeywords`)·`FavoritesContext`(`useFavorites`) 형태로 상태를 감싸 두었다. **1차 연동은 이 hook 내부 구현만 실제 API 호출로 바꾸면 되고, 화면(JSX) 쪽은 대부분 손댈 필요가 없다.**

**아직 결정·구현되지 않은 것 (1차 작업에서 채워야 함)**

- FE에 공통 API Client가 없다. `front/src/lib/auth.ts`는 `sessionStorage` 플래그 하나로만 로그인 여부를 흉내 내는 데모 코드다 (`RequireAuth.tsx`가 이걸 참조).
- FE `package.json`에 axios 등 별도 HTTP 라이브러리가 없다. 새로 추가하지 말고 **fetch 기반 공통 client**로 만든다 (의존성 추가가 필요하면 먼저 합의).
- BE `requirements.txt`에 비밀번호 해시·JWT 라이브러리가 없다 (`passlib[bcrypt]`, `PyJWT` 등). 인증 방식 확정 시 같이 추가한다.
- `users`(계정), `keywords`, `saved_announcements` 테이블이 Supabase와 `models.py` 어디에도 아직 없다. **Supabase에 테이블을 먼저 만들고 나서** `Announcement`와 같은 패턴(UUID PK `gen_random_uuid()`, 필요한 `UniqueConstraint`)으로 `models.py`에 추가한다.
- `SignupPage.tsx`를 보면 "사번 + 이름"으로 먼저 사원 여부를 인증하고(현재는 `20230001`/`김민준`만 통과하는 데모), 통과해야 비밀번호·이메일 입력이 열리는 2단계 구조다. 즉 회원가입 API는 **① 사번·이름 사원 인증 → ② 계정 생성(비밀번호·이메일)** 두 단계로 나눠야 한다.
- FE 타입(`front/src/types/index.ts`)의 `Announcement.id`, `Keyword.id`는 `number`인데, BE `Announcement.id`는 UUID(`str`)다. **DB가 기준이므로 FE 타입을 `string`으로 맞춘다.** (id 관련 작업에서 가장 놓치기 쉬운 불일치이니 API 계약 확정 때 반드시 짚고 넘어간다.)
- `.env.example`의 `FRONTEND_ORIGIN` 기본값은 `http://localhost:3000`이지만, 실제 Vite 개발 서버 포트는 `PORT`(기본 `8443`, `front/vite.config.ts`)다. `.env`의 `FRONTEND_ORIGIN`을 실제 FE 접속 주소로 맞춰야 CORS가 열린다.

---

## 1. 목표

FE와 BE가 아직 실제 데이터로 연결되지 않은 상태이므로, 1차 작업은 각 파트가 기능을 따로 완성하는 방식이 아니라 **연동 기반부터 만들고 기능 하나씩 실제로 연결하는 방식**으로 진행한다.

중간 점검에서는 다음 사용자 흐름을 실제 화면과 Supabase 데이터로 시연한다.

> 회원가입(사원 인증 → 계정 생성) → 로그인 → 공고 목록·검색·정렬 → 공고 상세 → 공고 저장 → 키워드 등록 → 새로고침·재로그인 후 저장값 확인

---

## 2. 진행 원칙

1. FE와 BE가 API 규칙을 먼저 맞춘다. (BE는 기존에 만든 `{success, data}` 포맷을 그대로 유지)
2. BE가 API 하나를 완성하면 Swagger(`/docs`)나 Postman으로 먼저 확인한다.
3. 확인된 API를 FE가 즉시 연결한다. 이때 화면을 새로 만들지 말고, **기존 hook(`useKeywords`, `useFavorites`) 내부만 mock 데이터 → API 호출로 교체**한다.
4. 연결이 끝난 기능은 FE·BE가 함께 정상·오류 시나리오를 점검한다.
5. 모든 BE 기능을 만든 뒤 한꺼번에 FE와 연결하지 않는다.
6. 기능별 연동 완료 여부를 확인한 뒤 다음 기능으로 넘어간다.

---

## 3. 전체 작업 순서

| 순서 | 담당 | 작업 | 선행 작업 | 완료 및 연동 확인 기준 |
| :---: | :---: | --- | --- | --- |
| 1 | FE·BE | API 계약 확정 (id 타입 포함) | 없음 | 요청·응답 필드, id 타입(UUID string), 오류 형식, 인증 방식, 날짜·상태값, 정렬값 합의 |
| 2 | BE | 서버 연결 기반 점검 | 1 | `/api/v1/health` 정상 응답, `.env`의 `FRONTEND_ORIGIN`을 FE 실제 접속 주소로 설정 |
| 3 | FE | 공통 API Client(`lib/api.ts`) 신설 | 1, 2 | fetch 기반 Base URL·공통 오류처리로 `/api/v1/health` 호출 성공 |
| 4 | BE | 사원 인증 + 회원가입 API·Supabase 저장 | 1, `users` 테이블 준비 | 사번·이름 사전 인증 → 통과 시에만 계정 생성, 비밀번호 해시 저장, 중복 가입 차단 |
| 5 | FE·BE | 회원가입 화면(`SignupPage.tsx`) 연동 | 3, 4 | 데모 하드코딩(`20230001`/`김민준`) 제거, 실제 인증 API 결과로 `verifyState` 결정, Supabase 저장 확인 |
| 6 | BE | 로그인·세션 API | 4 | 가입 계정 검증, 토큰 발급·검증, 로그아웃·인증 오류 처리 |
| 7 | FE·BE | 로그인·인증 상태 연동 | 3, 6 | `lib/auth.ts`를 실제 토큰 기반으로 교체, `RequireAuth.tsx`가 실제 인증 상태로 동작 |
| 8 | BE | 공고 목록·검색·정렬·상세 API 확장 | 1 | 기존 `GET /api/v1/announcements`에 검색어·필터·정렬·페이지네이션·상세(`/announcements/{id}`)·404 추가 |
| 9 | FE·BE | 공고 목록·상세 화면 연동 | 3, 7, 8 | `data/mock/announcements.ts` 대신 실제 API 응답 사용, `types/index.ts`의 id를 string으로 수정 |
| 10 | BE | 키워드 CRUD·Supabase 저장 | 7, `keywords` 테이블 준비, DB 무결성·RLS | 인증 사용자별 키워드 등록·조회·삭제·중복 방지 |
| 11 | FE·BE | 키워드 화면 연동 | 3, 10 | `useKeywords` 내부를 실제 API 호출로 교체, 새로고침·재로그인해도 키워드 유지 |
| 12 | BE | 저장공고 CRUD·Supabase 저장 | 7, 8, `saved_announcements` 테이블 준비, DB 무결성·RLS | 사용자별 공고 저장·취소·목록 조회·중복 방지 |
| 13 | FE·BE | 저장공고 화면 연동 | 3, 9, 12 | `useFavorites` 내부를 실제 API 호출로 교체, 저장 상태가 실제 DB 값과 일치 |
| 14 | FE·BE | 오류·권한·데이터 유지 점검 | 5, 7, 9, 11, 13 | 중복·미인증·권한·빈 결과·API 실패와 재로그인 시나리오 통과 |
| 15 | FE·BE·PM | 중간 점검 시연 리허설 | 14 | 테스트 계정·공고·키워드 준비, 전체 시연 흐름 중단 없이 통과 |

---

## 4. 1단계 — FE·BE 연동 기반

### 순서 1. API 계약 확정

코드 작성 전에 FE와 BE가 다음 항목을 함께 확정한다.

| 항목 | 확정할 내용 |
| --- | --- |
| API 주소 | 모두 `/api/v1` 하위: 사원인증·회원가입·로그인·로그아웃·공고 목록·상세·키워드·저장공고 |
| id 타입 | Supabase PK는 UUID → 모든 리소스 id는 문자열(string)로 주고받는다. FE `types/index.ts`도 이에 맞춘다 |
| 필드명 | `empId`(사번)·`name`·`email`·`pw` 등 FE 화면에서 이미 쓰는 이름을 그대로 API 필드명으로 맞춘다 |
| 성공 응답 | 기존 관례 유지: `{"success": true, "data": ...}` (목록은 `data`가 배열, 필요 시 `meta`에 전체 건수·페이지 정보) |
| 오류 응답 | 기존 성공 포맷과 짝을 맞춘 `{"success": false, "error": {"code", "message"}}` |
| 인증 | 토큰 발급 방식, 요청 헤더, 만료·로그아웃 처리 |
| 날짜 | 날짜 문자열 형식과 타임존 처리 방식 (BE는 이미 `date`/`datetime` 그대로 반환 중 — JSON 직렬화 형식 합의 필요) |
| 공고 상태 | `types/index.ts`의 `StatusType`(`접수중`/`접수예정`/`마감임박`/`마감`)과 BE `Announcement.status` 허용값 일치 |
| 정렬 | `latest`, `deadline`, `title` 값과 DB 정렬 기준 |

권장 오류 응답 예시:

```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_EMAIL",
    "message": "이미 등록된 이메일입니다."
  }
}
```

### 순서 2. BE 연결 기반 점검

`/api/v1/health`, CORS, 환경변수 로딩은 이미 되어 있으므로 새로 만들지 않고 아래만 점검한다.

- `back/.env`의 `FRONTEND_ORIGIN`을 FE가 실제로 뜨는 주소(`http://localhost:8443` 등, `PORT` 값에 맞춰)로 설정
- `DATABASE_URL`, `DATA_GO_KR_API_KEY` 등 필요한 값이 로컬 `.env`에 채워져 있는지 확인
- `GET /api/v1/health/db`로 Supabase 연결까지 확인

### 순서 3. FE 공통 API Client(`lib/api.ts`) 신설

`front/src/lib/`에 `auth.ts`만 있고 API 호출용 client는 없다. 새 파일(`front/src/lib/api.ts` 등)로 만든다.

- API Base URL은 환경변수(`import.meta.env.VITE_API_BASE_URL`)로 분리
- fetch 기반 공통 요청 함수 (axios 등 새 의존성 추가는 팀 합의 후에만)
- 인증 토큰 자동 첨부 준비
- 401 응답 시 인증 상태 초기화 (`lib/auth.ts`와 연결)
- 공통 Loading·Error 처리
- `/api/v1/health` 호출 성공을 FE 연동의 첫 번째 완료 기준으로 삼는다

---

## 5. 2단계 — 회원가입·로그인 연동

### 순서 4. BE 사원 인증 + 회원가입 API

`SignupPage.tsx`의 2단계 흐름(사원 인증 → 계정 생성)에 맞춰 API도 두 단계로 나눈다.

구현 내용:

- **사원 인증**: 사번+이름을 기존 사원 명부(별도 테이블 또는 Supabase에 이미 있는 데이터)와 대조해 일치 여부만 반환 (데모 하드코딩 `20230001`/`김민준` 대체)
- **계정 생성**: 사원 인증을 통과한 사번에 한해 이메일·비밀번호로 계정 생성
- 사번·이메일 중복 가입 확인
- 비밀번호는 해시로 저장 (평문 저장 금지 — `passlib[bcrypt]` 등 라이브러리 추가 필요)
- 회원가입 성공·중복·입력 오류·DB 오류 응답 처리

완료 기준:

- 사원 명부에 없는 사번·이름 조합은 인증 단계에서 걸러진다.
- 인증을 통과한 사용자만 계정이 Supabase에 생성된다.
- 동일 사번·이메일로 다시 가입할 수 없다.

### 순서 5. FE 회원가입 연동

구현 내용:

- `SignupPage.tsx`의 `handleVerify` 내부 데모 로직(`setTimeout` + 하드코딩 비교)을 실제 사원 인증 API 호출로 교체
- 회원가입 버튼 중복 클릭 방지
- 실제 BE 계정 생성 API 호출
- 중복 사번·이메일·입력 오류 메시지 표시
- 성공 시 기존과 동일하게 `/signup/done`으로 이동

공동 연동 확인:

> FE 사번·이름 입력 → BE 사원 인증 → FE 비밀번호·이메일 입력 → BE 계정 생성 → Supabase 저장 → FE 성공 처리

### 순서 6. BE 로그인·세션 API

구현 내용:

- 가입한 계정의 사번·비밀번호 검증
- JWT 또는 세션 발급·검증
- 로그아웃
- 토큰 만료·위조·미인증 요청 처리

### 순서 7. FE 로그인·인증 상태 연동

`lib/auth.ts`(`sessionStorage` 플래그)와 `RequireAuth.tsx`를 실제 인증 상태 기반으로 바꾼다.

구현 내용:

- `LoginPage.tsx`에서 실제 로그인 API 호출 (`login()` 함수 내부 교체)
- 토큰 저장 방식 결정 (예: `sessionStorage`에 플래그 대신 토큰 자체 저장)
- `RequireAuth.tsx`의 `isAuthenticated()`가 실제 토큰 유효성을 반영하도록 수정
- 로그인 실패·만료 메시지 표시
- 로그아웃 시 사용자정보와 토큰 제거

공동 완료 기준:

- 방금 가입한 계정으로 로그인할 수 있다.
- 로그인 사용자만 보호 화면(`RequireAuth`로 감싼 라우트)과 개인화 API에 접근할 수 있다.
- 로그아웃 후 보호 화면에 접근할 수 없다.

---

## 6. 3단계 — 공고 화면 연동

### 순서 8. BE 공고 API 확장

기존 `GET /api/v1/announcements`(`back/app/api/v1/announcements.py`)는 `limit`/`source` 필터만 있는 단순 목록이다. 여기에 기능을 추가한다.

구현 내용:

- 검색어·상태·기관 필터 추가
- 최신순·마감순·제목순 정렬 추가
- 페이지네이션과 전체 건수 반환
- 공고 ID(UUID) 기준 상세 조회 엔드포인트 신설
- 존재하지 않는 공고 404 처리
- 상태·D-Day·원문 링크 반환 (D-Day는 FE가 계산할지 BE가 내려줄지 먼저 합의)

정렬 권장 기준:

| FE 요청값 | DB 정렬 기준 |
| --- | --- |
| `latest` | `reception_start DESC, id DESC` |
| `deadline` | `reception_end ASC NULLS LAST, id ASC` |
| `title` | `title ASC, id ASC` |

### 순서 9. FE 공고 목록·상세 연동

구현 내용:

- `data/mock/announcements.ts`를 실제 API 결과로 교체 (`SearchPage`, `DashboardPage`의 `MatchedFeed`/`SavedList`, `ResultsTable`이 참조하는 `Announcement[]`)
- `types/index.ts`의 `Announcement.id`를 `number` → `string`(UUID)으로 수정하고 참조하는 곳 함께 수정
- 검색·필터·정렬 조건을 API 요청에 반영
- 페이지 변경 시 해당 범위를 다시 요청
- 목록에서 상세 화면(`DetailModal.tsx`)으로 공고 ID 전달
- Loading·Empty·Error 상태 처리

공동 완료 기준:

- 실제 DB 공고가 화면에 표시된다.
- 검색·정렬·페이지 변경 시 FE 화면과 BE 조회 조건이 일치한다.
- 공고 상세 화면과 원문 링크가 정상 동작한다.

---

## 7. 4단계 — 키워드 연동

### 순서 10. BE 키워드 API

`keywords` 테이블을 Supabase에 먼저 만들고, `models.py`에 `Announcement`와 같은 패턴으로 모델을 추가한다.

구현 내용:

- 인증 사용자 키워드 목록 조회
- 키워드 등록·삭제
- 공백·길이·중복 검증
- 사용자 ID를 인증 토큰에서 확인
- 사용자별 RLS와 소유권 검증

### 순서 11. FE 키워드 화면 연동

`useKeywords`(`front/src/hooks/useKeywords.ts`)의 내부 구현만 교체하고, `KeywordsContext`를 쓰는 화면(`MyPage/KeywordsTab.tsx` 등)은 그대로 둔다.

구현 내용:

- 로그인 후 키워드 목록 조회로 초기 상태 채우기 (`INITIAL_KEYWORDS` mock 제거)
- `addKeyword`/`removeKeyword`/`toggleAlert`를 실제 API 호출로 교체
- 요청 중 버튼 중복 클릭 방지
- 중복·입력 오류 메시지 표시
- 성공 후 서버 데이터 재조회

공동 완료 기준:

- 사용자별 키워드가 Supabase에 저장된다.
- 새로고침·로그아웃·재로그인 후에도 유지된다.
- 다른 사용자의 키워드를 조회·삭제할 수 없다.

---

## 8. 5단계 — 저장공고 연동

### 순서 12. BE 저장공고 API

`saved_announcements` 테이블을 Supabase에 먼저 만들고, `models.py`에 모델을 추가한다.

구현 내용:

- 인증 사용자의 공고 저장
- 저장 취소
- 사용자별 저장공고 목록 조회
- 사용자 ID·공고 ID(UUID) FK 검증
- 사용자·공고 조합의 중복 저장 방지 (UNIQUE 제약)
- 다른 사용자의 저장 데이터 접근 차단

### 순서 13. FE 저장공고 화면 연동

`useFavorites`(`front/src/hooks/useFavorites.ts`)의 내부 구현만 교체한다.

구현 내용:

- 초기 저장 목록을 mock(`ANNOUNCEMENTS.filter(a => a.isFavorite)`) 대신 API로 조회
- `toggleFavorite`을 저장/취소 API 호출로 교체
- 저장 여부에 따른 버튼 상태 표시 (`DetailModal`, `ResultsTable`, `SavedList`)
- 저장 성공 응답 전에 화면 상태를 확정하지 않음

공동 완료 기준:

- 공고 저장·취소가 Supabase 데이터와 일치한다.
- 새로고침·재로그인 후 저장 상태가 유지된다.
- 동일 공고가 중복 저장되지 않는다.

---

## 9. 6단계 — 통합 점검과 시연 준비

### 순서 14. 오류·권한·영속성 점검

| 시나리오 | 예상 결과 |
| --- | --- |
| 사원 명부에 없는 사번·이름 | 사원 인증 단계에서 차단 |
| 중복 사번·이메일 가입 | 가입 차단 및 명확한 오류 표시 |
| 잘못된 비밀번호 | 로그인 실패 메시지 표시 |
| 토큰 없이 개인화 API 호출 | 401 응답 |
| 다른 사용자의 데이터 접근 | 403 또는 조회 결과 없음 |
| 존재하지 않는 공고 상세 | 404 응답 |
| 중복 키워드·저장공고 등록 | 중복 차단 |
| 검색 결과 없음 | 빈 배열과 Empty UI 표시 |
| BE 또는 네트워크 오류 | Error UI와 재시도 가능 상태 |
| 새로고침·재로그인 | DB에 저장한 키워드·저장공고 유지 |

### 순서 15. 중간 점검 시연 리허설

1. 사원 명부에 있는 사번·이름으로 사원 인증 후 비밀번호·이메일을 등록해 회원가입한다.
2. Supabase에 계정 정보가 저장됐는지 확인한다.
3. 방금 가입한 계정으로 로그인한다.
4. 공고 목록이 기본 최신순으로 표시되는지 확인한다.
5. 마감 임박순으로 변경하고 검색·필터를 적용한다.
6. 공고 상세 화면에서 기간·상태·D-Day·원문 링크를 확인한다.
7. 공고를 저장한다.
8. 키워드를 등록한다.
9. 로그아웃 후 다시 로그인한다.
10. 키워드와 저장공고가 그대로 유지되는지 확인한다.

---

## 10. 병렬 진행 가능 구간

순서를 지키되 다음 작업은 병렬로 진행할 수 있다.

| BE 작업 | 동시에 가능한 FE 작업 | 합류 시점 |
| --- | --- | --- |
| 사원 인증·회원가입·로그인 API 구현 | `lib/api.ts` 공통 client, `SignupPage`/`LoginPage`의 API 호출 부분만 미리 분리 | BE Swagger/Postman 테스트 통과 직후 |
| 공고 API 확장 | 합의한 응답 구조로 `types/index.ts` id 타입 수정, 목록/상세 컴포넌트 정리 | 공고 목록 API 테스트 통과 직후 |
| 키워드 API 구현 | `useKeywords` 내부를 API 호출 형태로 리팩터링 준비 | 키워드 조회·등록 API 테스트 통과 직후 |
| 저장공고 API 구현 | `useFavorites` 내부를 API 호출 형태로 리팩터링 준비 | 저장·취소 API 테스트 통과 직후 |

> 병렬 작업은 가능하지만, 각 기능의 BE 테스트가 끝나면 즉시 FE와 연결하여 계약 불일치(특히 id 타입)를 확인한다.

---

## 11. 1차 완료 체크리스트

### 연동 기반

- [ ] FE·BE 요청·응답·오류·인증 규칙과 id 타입(UUID string)이 문서로 확정되어 있다.
- [ ] FE에 `lib/api.ts` 공통 client가 생겼고 `/api/v1/health` 호출에 성공한다.
- [ ] `.env`의 `FRONTEND_ORIGIN`이 실제 FE 접속 주소와 일치해 CORS가 정상 적용된다.

### 회원가입·로그인

- [ ] 사원 명부에 없는 사번·이름은 인증 단계에서 걸러진다.
- [ ] 회원가입 정보가 Supabase에 저장된다.
- [ ] 비밀번호가 평문으로 저장되지 않는다.
- [ ] 사번·이메일 중복 가입이 차단된다.
- [ ] `lib/auth.ts`가 실제 토큰 기반으로 동작하며, 가입한 계정으로 로그인·로그아웃할 수 있다.
- [ ] 미인증 사용자의 보호 API 접근이 차단된다.

### 공고

- [ ] `data/mock/announcements.ts` 없이 실제 공고가 화면에 표시된다.
- [ ] 검색·필터·정렬·페이지 이동이 API와 연결된다.
- [ ] 공고 상세와 원문 링크가 동작한다.
- [ ] Loading·Empty·Error 상태가 표시된다.

### 키워드·저장공고

- [ ] `useKeywords`/`useFavorites`가 mock 데이터 없이 실제 API로 동작한다.
- [ ] 키워드 등록·조회·삭제가 사용자별로 동작한다.
- [ ] 공고 저장·취소·목록 조회가 사용자별로 동작한다.
- [ ] 중복 키워드와 중복 저장공고가 차단된다.
- [ ] 다른 사용자의 데이터에 접근할 수 없다.
- [ ] 새로고침·재로그인 후 데이터가 유지된다.

### 중간 점검

- [ ] 전체 시연 시나리오가 중단 없이 통과한다.
- [ ] 시연용 테스트 계정(사원 명부 등록분)과 실제 공고 데이터가 준비되어 있다.
- [ ] 시연을 막는 P0 오류가 없다.

# 통합 후 E2E 재리허설 (main 기준)

> 6주차 리허설(`6th_wk_E2E_리허설.md`)은 **FE는 작업 브랜치 / BE는 main**인 혼합 조합이었다.
> 이 문서는 통합 방향 결정에 따라 **FE·BE 모두 main 기준**으로 다시 실행한 기록이다.
> 실행일: 2026-09-05 / 실행자: FE

---

## 1. 실행 환경

| 구성 | 내용 |
|---|---|
| FE | `feature/fe-mypage-notifications` (= `origin/main` `a47d968` + 마이페이지·알림 이식분) |
| BE | `origin/main` `a47d968`, 임시 폴더에서 uvicorn `127.0.0.1:8000` |
| DB | 로컬 MySQL 8.0 `forward`, alembic 4개 리비전 적용 |
| 데이터 | 사원 1명 + 공고 5건 시드, 키워드 2개(`AI`, `데이터`), 알림 5건 |

브라우저 확장 미연결로 **UI 클릭 레벨은 이번에도 미실행**이다. API 레벨 + 정적 대조로 대체했다.

---

## 2. 정적 대조 — FE가 부르는 것과 BE가 가진 것

### 2-1. 경로

FE 소스에서 추출한 **API 경로 19개가 모두 BE 라우트에 존재**한다. 불일치 0건.

```
/admin/employees        /admin/employees/{id}   /admin/users        /admin/users/{id}
/announcements          /announcements/{id}     /auth/login         /auth/signup
/auth/verify-employee   /dashboard/summary      /keywords           /keywords/{id}
/me                     /me/change-password     /notifications      /notifications/{id}/read
/notifications/read-all /saved-announcements    /saved-announcements/{id}
```

> 추출 과정에서 `/admin`이 하나 더 잡혔는데 이건 API가 아니라 React Router 경로
> (`navigate('/admin')`)라 오탐이다.

### 2-2. 응답 필드

FE가 선언한 인터페이스와 BE 실제 응답의 키를 대조했다. **누락 0건.**

| FE 인터페이스 | 결과 |
|---|:---:|
| `ApiAnnouncement` (`lib/announcements.ts`) | ✅ |
| `dashboard.matched[]` / `saved[]` | ✅ |
| `dashboard.counts` | ✅ |
| `Me` (`types/index.ts`) | ✅ |
| `AppNotification` (`types/index.ts`) | ✅ |
| `ApiKeyword` (`hooks/useKeywords.ts`) | ✅ |

---

## 3. 사용자 흐름 — 15개 항목 전부 통과

| # | 단계 | 결과 |
|:--:|---|---|
| 1 | 사원 인증 | 200 `verified: true` |
| 2 | 로그인 | 200, `name`·`isAdmin` 포함 |
| 3 | 대시보드 | 200 `matched 4 / newToday 0 / urgent 1 / saved 1` |
| 4 | 검색 `q=AI` | 200 `total=2` |
| 5 | **상태 필터 `statusLabel=접수중` (서버측)** | 200 `total=2` |
| 6 | 공고 상세 | 200, `statusLabel` 정상 |
| 7 | 공고 저장 | 200 |
| 8 | 중복 저장 | 409 `ALREADY_SAVED` |
| 9 | 키워드 목록 | 200, 2건 |
| 10 | 마이페이지 내 정보 | 200 |
| 11 | **비밀번호 오답** | 401 `INVALID_CREDENTIALS` |
| 12 | **→ 직후 세션 유지 확인** | **200 — 로그아웃되지 않음** |
| 13 | 알림 목록 | 200, 5건 |
| 14 | 저장 취소 | 200 |
| 15 | 무인증 접근 | 401 `UNAUTHORIZED` |

**11~12번이 이번 통합의 핵심 검증이다.** 통합 전 main 코드였다면 `api.ts`가
`if (res.status === 401) logout()`으로 처리해 **비밀번호를 잘못 입력한 사용자가 그대로
로그아웃**됐다. 코드 분기를 넣은 뒤 세션이 유지되는 것을 확인했다.

---

## 4. 관리자 화면 — 7개 항목 전부 통과

main에만 있는 기능이라 6주차 리허설에서는 다루지 못했다. 이번에 처음 확인했다.
(`scripts/promote_admin.py`로 계정을 잠시 관리자로 올려 검증하고, 끝난 뒤 `is_admin=0`으로 원복했다.)

| # | 단계 | 결과 |
|:--:|---|---|
| 1 | 사원 명부 목록 | 200, `joined` 플래그 정상 |
| 2 | 사원 등록 | 200 |
| 3 | 중복 사번 등록 | 409 `DUPLICATE_EMP_ID` |
| 4 | 가입자 목록 | 200 |
| 5 | 가입한 사원 삭제 시도 | 409 `EMPLOYEE_ALREADY_JOINED` |
| 6 | 미가입 사원 삭제 | 200 |
| 7 | 없는 사원 삭제 | 404 `EMPLOYEE_NOT_FOUND` |

---

## 5. 6주차 대비 달라진 점

| 항목 | 6주차 | 이번 |
|---|---|---|
| FE 기준 | 작업 브랜치 | **main + 이식분** |
| 관리자 화면 | 미검증 | **7항목 검증** |
| 서버측 상태 필터 | 브랜치 구현으로 검증 | **main 구현으로 재검증** |
| 401 코드 분기 | 브랜치에만 있었음 | **main에 이식 후 검증** |

---

## 6. 남은 범위

| 항목 | 상태 |
|---|---|
| UI 클릭 레벨 리허설 | ⬜ 브라우저 확장 미연결 |
| 마이페이지 알림 설정(`AlertsTab`) | ⬜ `alert_settings` API 부재 |
| `dashboard/summary`의 `newToday` 타임존 버그 | 🔴 BE 미수정 (`6th_wk_E2E_리허설.md` 3.3절) |
| 저장공고 응답에 `statusLabel` 추가 | 🔵 BE 요청 대기 |
| 06:00 파이프라인 실제 실행 | ⚙️ 코드는 연결됨. `DATA_GO_KR_API_KEY`·`SMTP_*` 설정 후 검증 필요 |

### 이번 리허설 중 발견한 것

**`announcements.ts`가 `postedDate`와 `receiptDate`에 둘 다 `reception_start`를 넣는다.**
검색 결과 표의 "게시일" 컬럼과 상세 모달의 접수 시작일이 같은 값을 보여준다.
BE의 `collected_at`은 인터페이스에 선언만 되고 쓰이지 않는다. 통합 범위 밖이라 손대지 않았고,
별도 항목으로 남긴다.

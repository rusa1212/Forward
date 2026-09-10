# 알림 설정 API 제안 (`alert_settings`)

> 작성: FE / 2026-09-05
> 대상: 진행상황 md의 **"P1 마이페이지 알림 설정 탭"** — FE에서 유일하게 남은 미연동 화면
> 성격: **제안서**다. BE 구현 전이므로 이 문서의 스키마·엔드포인트는 확정이 아니다.
> 확정되면 `docs/api-contract-v1.md`에 정식 절로 옮긴다.

---

## 1. 왜 필요한가

`front/src/pages/MyPage/AlertsTab.tsx`는 지금 **저장 버튼이 API를 부르지 않는다.** 값이 전부
React state와 `useKeywords`의 로컬 ref에만 있어서 **새로고침하면 초기화된다.**

FE 혼자 할 수 있는 건 다 했다 — 화면에 "저장 API가 없어 새로고침하면 초기화됩니다" 경고를 달고,
저장 버튼 문구도 "저장되었습니다" → "화면에만 반영되었습니다"로 고쳐 사용자를 속이지 않게 해뒀다.
**서버에 저장할 곳이 생기면 FE 연동은 반나절이면 끝난다.**

---

## 2. 저장해야 하는 값

화면에 실제로 존재하는 컨트롤을 전부 옮긴 것이다. 임의로 추가한 값은 없다.

### 2-1. 키워드별 (키워드 1개당 1행)

| 값 | 화면 위치 | 타입 | 현재 FE 기본값 | 의미 |
| --- | --- | --- | --- | --- |
| `dashboardAlert` | AlertsTab 섹션1 표 | bool | `true` | 이 키워드 매칭 시 대시보드/헤더 알림 생성 |
| `emailAlert` | AlertsTab 섹션1 표 | bool | `false` | 이 키워드 매칭 시 이메일 발송 대상에 포함 |

> 현재 `mappers.ts`의 `mapKeyword()`가 이 두 값을 `true`/`false`로 하드코딩하고 있다.
> API가 생기면 서버 값으로 대체한다.

### 2-2. 사용자별 (사용자 1명당 1행)

| 값 | 화면 위치 | 타입 | 현재 FE 기본값 | 의미 |
| --- | --- | --- | --- | --- |
| `emailFrequency` | "이메일 발송 시간" | `daily` \| `weekly` | `daily` | `daily`=매일 09시, `weekly`=월요일 1회 |
| `deadlineAlertDays` | "마감 임박 기준일" | `7` \| `3` \| `1` | `7` | 저장공고 마감 며칠 전부터 알릴지 |
| `deadlineDashboardAlert` | "알림 채널" 대시보드 | bool | `true` | 마감임박을 대시보드 알림으로 |
| `deadlineEmailAlert` | "알림 채널" 이메일 | bool | `false` | 마감임박을 이메일로 |

---

## 3. 제안 스키마

키워드별 값과 사용자별 값은 수명이 다르다(키워드는 지워지고 사용자 설정은 남는다).
그래서 **테이블을 나누지 말고, 키워드별 2개는 `keywords` 테이블에 컬럼으로 붙이는 것**을 제안한다.
별도 테이블을 만들면 키워드 CRUD마다 join·정리가 따라붙는데 컬럼 2개에 비해 이득이 없다.

```python
# app/db/models.py — Keyword 에 컬럼 2개 추가
class Keyword(Base):
    ...
    dashboard_alert: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    email_alert:     Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))


# app/db/models.py — 사용자별 설정 (1:1)
class AlertSetting(Base):
    __tablename__ = "alert_settings"

    user_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    email_frequency:          Mapped[str]  = mapped_column(String(10), nullable=False, server_default=text("'daily'"))
    deadline_alert_days:      Mapped[int]  = mapped_column(Integer,    nullable=False, server_default=text("7"))
    deadline_dashboard_alert: Mapped[bool] = mapped_column(Boolean,    nullable=False, server_default=text("1"))
    deadline_email_alert:     Mapped[bool] = mapped_column(Boolean,    nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.utc_timestamp(), onupdate=func.utc_timestamp()
    )
```

- `alert_settings`의 PK를 `user_id`로 두면 1:1이 스키마로 보장된다(별도 UNIQUE 불필요).
- **행이 없는 사용자는 기본값으로 취급**한다. 회원가입 시 미리 만들지 않아도 되고,
  조회 시 없으면 기본값 객체를 돌려주면 된다(4-1 참고). 기존 가입자 마이그레이션도 불필요하다.
- `server_default`를 걸어두면 기존 키워드 행도 자동으로 `dashboard_alert=1, email_alert=0`이 된다.

---

## 4. 제안 API

`me.py`와 같은 결로 `/me` 하위에 두는 것을 제안한다. **모두 토큰 필요.**

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `GET` | `/me/alert-settings` | 사용자별 설정 조회 |
| `PUT` | `/me/alert-settings` | 사용자별 설정 저장 (전체 교체) |
| `PATCH` | `/keywords/{id}/alerts` | 키워드 1개의 알림 토글 |

### 4-1. `GET /me/alert-settings`

```json
{
  "success": true,
  "data": {
    "emailFrequency": "daily",
    "deadlineAlertDays": 7,
    "deadlineDashboardAlert": true,
    "deadlineEmailAlert": false
  }
}
```

**행이 없으면 오류가 아니라 위 기본값을 그대로 내려준다.** FE는 조회 실패와 "아직 저장한 적 없음"을
구분할 필요가 없어진다.

### 4-2. `PUT /me/alert-settings`

요청 본문은 4개 필드 전부(부분 수정이 아니라 전체 교체). 화면의 저장 버튼이 4개를 한 번에 보내므로
`PATCH`보다 `PUT`이 화면 동작과 맞는다. 응답은 4-1과 같은 갱신된 객체.

| HTTP | `code` | 상황 |
| :---: | --- | --- |
| 422 | `VALIDATION_ERROR` | `emailFrequency`가 `daily`/`weekly`가 아님, `deadlineAlertDays`가 7/3/1이 아님 |

> `deadlineAlertDays`를 7/3/1로 **제한할지**는 결정이 필요하다(6-3 참고).
> 자유 정수로 열어둘 거면 `1~30` 정도의 범위 검증을 제안한다.

### 4-3. `PATCH /keywords/{id}/alerts`

```jsonc
// 요청 — 바꾸려는 것만 보낸다
{ "dashboardAlert": false }

// 응답 — 키워드 객체 (기존 GET /keywords 형태 + 토글 2개)
{
  "success": true,
  "data": {
    "id": "...", "keyword": "AI", "createdAt": "...",
    "dashboardAlert": false, "emailAlert": false
  }
}
```

| HTTP | `code` | 상황 |
| :---: | --- | --- |
| 404 | `KEYWORD_NOT_FOUND` | 없는 키워드 또는 **남의 키워드** (기존 규칙과 동일) |

**`GET /keywords`·`POST /keywords` 응답에도 `dashboardAlert`/`emailAlert`를 추가**해야 한다.
그래야 FE가 목록 조회 한 번으로 표를 그릴 수 있다.

---

## 5. notifier 연동 — 설정을 실제로 쓰는 지점

설정만 저장하고 발송 로직이 안 읽으면 의미가 없다. `services/notifier.py`에서 다음을 반영해야 한다.

| 함수 | 반영할 것 |
| --- | --- |
| `generate_keyword_match_notifications()` | 키워드 루프에서 **`dashboard_alert = false`인 키워드는 건너뛴다** (알림 자체를 만들지 않음) |
| `send_pending_notification_emails()` | **`email_alert = true`인 키워드에서 나온 알림만** 이메일 대상에 포함 |
| 〃 | `email_frequency = weekly`인 사용자는 **월요일에만** 발송 |
| 마감임박 알림 생성 | 판정 기준을 전역 `DEADLINE_SOON_DAYS`가 아니라 **사용자의 `deadline_alert_days`** 로 |
| 〃 | `deadline_dashboard_alert = false`면 마감임박 알림을 만들지 않음 |

> 현재는 이 값들이 없어서 **모든 키워드·모든 사용자에게 무조건** 알림을 만들고,
> `send_pending_notification_emails()`는 `emailed_at IS NULL`인 알림을 사용자별로 묶어 전부 보낸다.

**구현 시 걸릴 지점 하나** — 이메일 필터를 `keyword.email_alert`로 걸려면 알림의 `keyword_id`를
join해야 하는데, **6-1을 A안으로 가면 저장공고 마감임박 알림은 `keyword_id`가 `NULL`이다.**
그 알림은 키워드 설정이 아니라 사용자 설정 `deadline_email_alert`로 판단해야 한다. 정리하면:

| 알림 | 대시보드 표시 여부 | 이메일 발송 여부 |
| --- | --- | --- |
| `신규매칭` (keyword_id 있음) | `keyword.dashboard_alert` | `keyword.email_alert` |
| `마감임박` — 키워드 출처 | `keyword.dashboard_alert` | `keyword.email_alert` |
| `마감임박` — 저장공고 출처 (A안) | `deadline_dashboard_alert` | `deadline_email_alert` |

---

## 6. 결정이 필요한 쟁점

### 6-1. 🔴 "즐겨찾기 마감 임박"인데 실제로는 키워드 마감임박이다

화면 섹션2 제목은 **"즐겨찾기 마감 임박 알림"** 이고 설명도 *"즐겨찾기한 공고의 마감일이 다가오면"* 이다.
그런데 `notifier.py`가 만드는 `notify_type="마감임박"` 알림은 **키워드에 매칭된 공고**에 대한 것이고
`keyword_id`가 붙는다. **저장공고(`saved_announcements`)는 쳐다보지도 않는다.**

즉 사용자가 저장해둔 공고가 내일 마감이어도, 그 공고가 내 키워드에 안 걸리면 알림이 안 온다.
**화면이 약속하는 동작과 서버 동작이 다르다.** 셋 중 하나를 골라야 한다.

| 안 | 내용 |
| --- | --- |
| **A (화면대로)** | 저장공고 기준으로 마감임박 알림을 만든다. `notifier`에 `saved_announcements` 루프 추가 |
| B (서버대로) | 화면 문구를 "키워드 매칭 공고 마감 임박"으로 고친다 |
| C (둘 다) | 두 출처 모두 알림 생성. `notify_type`을 `마감임박-저장` / `마감임박-키워드`로 분리 |

FE 의견으로는 **A**를 권한다. 저장은 사용자가 "이건 챙기겠다"고 명시한 행동이라 마감 알림의 대상으로
가장 자연스럽고, 화면 문구·아이콘(별표)도 이미 그렇게 만들어져 있다.

### 6-2. 🔶 `deadlineAlertDays`와 `statusLabel`의 마감임박은 다른 개념이다

`announcements.py`의 `DEADLINE_SOON_DAYS = 3`은 **공고 목록 배지에 쓰는 표시용 전역 기준**이고,
`deadlineAlertDays`(7/3/1)는 **사용자가 언제 알림을 받을지 고르는 개인 설정**이다.
같은 이름("마감임박")을 쓰지만 섞으면 안 된다.
`notifier`가 마감임박 알림을 만들 때는 **전역값이 아니라 사용자 설정값**을 봐야 한다.

### 6-3. 🔶 `deadlineAlertDays`를 7/3/1로 제한할까

지금 화면은 버튼 3개다. 스키마는 정수라 값 자체는 자유롭게 넣을 수 있다.
FE는 **어느 쪽이든 대응 가능**하다 — 제한하면 타입을 `7 | 3 | 1`로 좁히고, 열어두면 숫자 입력으로 바꾼다.
BE 검증 정책만 정해주면 된다.

### 6-4. ⬜ `matchCount`는 이 범위 밖이다

`Keyword.matchCount`도 지금 `mapKeyword()`에서 `0`으로 하드코딩돼 있다.
다만 이건 **설정이 아니라 집계값**이라 `alert_settings`와 성격이 다르다.
`GET /keywords` 응답에 키워드별 매칭 건수를 얹어주는 방식이 자연스럽고,
`dashboard.py`가 이미 쓰는 `title ILIKE` 매칭을 재사용하면 된다. 별도 논의 대상.

---

## 7. 이 API가 나오면 FE가 하는 일

1. `endpoints.ts`에 `fetchAlertSettings` / `saveAlertSettings` / `updateKeywordAlerts` 추가
2. `useAlertSettings` 훅 신설 (조회·저장·pending·error — `useMe`와 같은 구조)
3. `AlertsTab`의 `useState` 4개를 훅 값으로 교체, 저장 버튼에 `PUT` 연결
4. `useKeywords`의 `alertsRef` **로컬 상태 보관 로직 삭제**, `toggleAlert`을 `PATCH` 호출로 교체
5. `mapKeyword()`의 하드코딩(`dashboardAlert: true, emailAlert: false`)을 서버 값으로 교체
6. 화면의 "저장 API가 없어 새로고침하면 초기화됩니다" 경고 문구 제거
7. 새로고침 후 값이 유지되는지 확인 (= 진행상황 md의 완료 조건)

**BE 쪽 최소 작업량**: 마이그레이션 1개(컬럼 2 + 테이블 1), 엔드포인트 3개, `notifier.py` 조건 분기.
6-1을 A안으로 정하면 `notifier.py`에 저장공고 루프가 추가로 필요하다.

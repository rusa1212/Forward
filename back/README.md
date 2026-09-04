# forward-be

FastAPI 백엔드. 공공데이터포털 API로 공고 데이터를 수집해서 MySQL/MariaDB에 저장합니다.
(6주차에 Supabase(Postgres) → MySQL/MariaDB로 전환 — `docs/be/6th_wk_DB전환.md`)

## 폴더 구조

```
app/
  main.py              FastAPI 진입점, CORS 등록
  core/
    config.py           .env 읽는 설정값 (Settings)
    errors.py            공통 오류 응답 형식 ({"success": false, "error": {...}})
    scheduler.py         APScheduler — 하루 1회(기본 06:00) 공고 수집 + 알림 생성 + 이메일 발송 자동 실행
  db/
    session.py           SQLAlchemy 세션 (Depends(get_db)). mysql일 때 세션 time_zone=UTC 고정
    models.py             ORM 모델 6개 (employees/users/announcements/keywords/notification_logs/saved_announcements)
  services/
    collector.py          공공데이터포털 API 3종 호출 + 필드 정규화
    storage.py             수집 결과를 announcements 테이블에 upsert (INSERT ... ON DUPLICATE KEY UPDATE)
    notifier.py             키워드 매칭 → notification_logs 알림 생성 + 미발송 알림 이메일 발송 (SMTP 설정 시)
  api/v1/
    router.py             라우터 모음
    health.py              헬스체크 (/health, /health/db)
    collect.py              수집 트리거 (GET: 미리보기, POST: 저장)
    announcements.py        저장된 공고 재조회 (검색/필터/정렬/페이지네이션)
    auth.py                 사원 인증 + 회원가입/로그인/로그아웃 (JWT)
    keywords.py             키워드 CRUD (로그인 필요)
    saved_announcements.py   공고 저장/저장취소/조회 (로그인 필요)
    me.py                     마이페이지: 내 정보 조회/수정, 비밀번호 변경 (로그인 필요)
    admin.py                 관리자 전용: 사원 명부 등록/삭제, 가입자 목록/삭제 (관리자만)
    dashboard.py              대시보드 집계: 오늘 신규/키워드 매칭/마감임박/저장공고 수+목록 (로그인 필요)
    notifications.py          알림 목록 조회 + 읽음/전체읽음 처리 (로그인 필요, notification_logs 테이블)
alembic/                 DB 마이그레이션 (스키마 정본). alembic/versions/*.py
alembic.ini
scripts/
  promote_admin.py        최초 관리자 지정용 1회성 스크립트
postman/
  Forward_BE_API.postman_collection.json   Postman 컬렉션 (전체 엔드포인트 요청 모음)
requirements.txt
.env.example
dev-seed.sql             로컬 개발용 시드(데모 사원 1명) — 선택
```

## 실행 방법

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS/Linux

copy .env.example .env   # DATA_GO_KR_API_KEY, DATABASE_URL, JWT_SECRET 채우기

# DB 준비 — 방법 A (권장): Docker
#   Docker Desktop 설치 후 아래 한 줄. forward DB/계정까지 자동 생성됨.
#   처음이면 docs/온보딩-MySQL과-Docker.md (개념 설명 + 따라하기 + FAQ) 참고.
docker compose up -d --wait     # --wait: DB가 healthy 될 때까지 대기 (첫 실행 수십 초)
#
# DB 준비 — 방법 B: MySQL 직접 설치 (MySQL 8 / MariaDB 10.4+)
#   빈 데이터베이스 + 계정 생성 (아래 SQL을 mysql -u root -p 로 1회 실행)
#        create database forward default character set utf8mb4 collate utf8mb4_unicode_ci;
#        create user if not exists 'forward'@'localhost' identified by 'forward';
#        grant all privileges on forward.* to 'forward'@'localhost';  -- 로컬은 마이그레이션까지 이 계정으로
#        flush privileges;
#
# 스키마 적용 (A/B 공통)
.venv\Scripts\alembic upgrade head
# (선택) 데모 사원 시드 — PowerShell은 '<' 리다이렉션이 안 되므로 cmd /c "..."로 감싸서 실행
#   Docker(mac/cmd): docker exec -i forward-mysql mysql -uroot -proot --default-character-set=utf8mb4 forward < dev-seed.sql
#   Docker(PowerShell): cmd /c "docker exec -i forward-mysql mysql -uroot -proot --default-character-set=utf8mb4 forward < dev-seed.sql"
#   직접 설치: mysql -u root -p --default-character-set=utf8mb4 forward < dev-seed.sql

.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

`.env`의 `DATABASE_URL`은 `mysql+pymysql://forward:forward@localhost:3306/forward?charset=utf8mb4` 형식입니다
(`.env.example` 참고). MySQL 8의 기본 인증(caching_sha2_password) 때문에 `PyMySQL`과 함께 `cryptography`가 필요하며 requirements에 포함돼 있습니다.

`GET /api/v1/health/db`가 `{"db":"connected"}`를 주면 연결 성공입니다.

## DB 스키마 변경 (마이그레이션)

스키마는 `alembic/versions/*.py`가 정본입니다. `models.py`를 고친 뒤:

```bash
.venv\Scripts\alembic revision --autogenerate -m "무엇을 바꿨는지"
.venv\Scripts\alembic upgrade head        # 내 DB에 적용
```

팀원은 pull 후 `alembic upgrade head` 한 줄이면 동기화됩니다. 자세한 절차는 `docs/be/alembic-마이그레이션.md`.

## 확인된 엔드포인트

- `GET /api/v1/health` → 서버 상태
- `GET /api/v1/health/db` → DB 연결 확인
- `GET /api/v1/collect` → 3개 소스(K-Startup, 나라장터, 과기정통부) 수집 미리보기 (DB 저장 안 함)
- `POST /api/v1/collect` → 수집 후 `announcements` 테이블에 upsert (`source`+`external_id` 기준 중복 방지)
- `GET /api/v1/announcements` → 공고 목록 (쿼리: `q`(제목 검색), `status`, `statusLabel`(접수중/접수예정/마감임박/마감), `department`, `source`, `sort`(latest/deadline/title), `page`, `page_size`)
- `GET /api/v1/announcements/{id}` → 공고 상세 (없으면 404 `ANNOUNCEMENT_NOT_FOUND`)
- `POST /api/v1/auth/verify-employee` → `{empId, name}`이 사원 명부와 일치하는지 확인 (회원가입 1단계)
- `POST /api/v1/auth/signup` → `{empId, name, email, pw}`로 계정 생성 (회원가입 2단계, 사원 인증 재검증)
- `POST /api/v1/auth/login` → `{empId, pw}` 검증 후 로그인 토큰(JWT) 발급
- `POST /api/v1/auth/logout` → 상태 없는(stateless) JWT라 서버가 지울 게 없음 (FE가 토큰만 버리면 됨)
- `GET /api/v1/keywords` (로그인 필요) → 내 키워드 목록
- `POST /api/v1/keywords` (로그인 필요) → `{keyword}` 등록 (중복 409 `DUPLICATE_KEYWORD`)
- `DELETE /api/v1/keywords/{keyword_id}` (로그인 필요) → 키워드 삭제
- `GET /api/v1/saved-announcements` (로그인 필요) → 내가 저장한 공고 목록
- `POST /api/v1/saved-announcements` (로그인 필요) → `{announcementId}`로 공고 저장 (중복 저장 차단, 존재하지 않는 공고면 404)
- `DELETE /api/v1/saved-announcements/{announcementId}` (로그인 필요) → 저장 취소
- `GET /api/v1/admin/employees` (관리자 전용) → 사원 명부 전체 목록 (가입 여부 `joined` 포함)
- `POST /api/v1/admin/employees` (관리자 전용) → `{empId, name, department?}`로 사원 등록 (중복 409 `DUPLICATE_EMP_ID`)
- `DELETE /api/v1/admin/employees/{empId}` (관리자 전용) → 사원 삭제 (이미 가입한 사원이면 409 `EMPLOYEE_ALREADY_JOINED`)
- `GET /api/v1/admin/users` (관리자 전용) → 가입자(계정) 전체 목록
- `DELETE /api/v1/admin/users/{userId}` (관리자 전용) → 가입자 계정 삭제 (로그인 차단)

관리자 전용 API는 토큰 없으면 401, 로그인했지만 관리자가 아니면 403을 반환한다 (`app/api/v1/auth.py`의 `get_current_admin`). 최초 관리자는 `scripts/promote_admin.py <emp_id>`로 지정한다 (해당 사번으로 이미 회원가입까지 마친 계정이어야 함).
- `GET /api/v1/dashboard/summary` (로그인 필요) → `{counts: {matched, newToday, urgent, saved}, matched: [...], saved: [...]}`. `matched`는 내 키워드가 제목에 포함된 공고(최신순 상위 10건), `newToday`는 그중 오늘 수집된 것, `urgent`는 그중 마감임박(`statusLabel`) 상태인 것.
- `GET /api/v1/me` (로그인 필요) → 내 정보(`empId`, `name`, `department`, `email`) 조회. 이름/부서는 `employees` 명부 기준
- `PATCH /api/v1/me` (로그인 필요) → `{email}`로 이메일 변경 (중복 시 409 `DUPLICATE_EMAIL`). 이름/연락처/아이디는 현재 스키마에 없어 이번 범위 밖
- `POST /api/v1/me/change-password` (로그인 필요) → `{currentPw, newPw}`로 비밀번호 변경 (현재 비밀번호 불일치 시 401 `INVALID_CREDENTIALS`)
- `GET /api/v1/notifications` (로그인 필요) → `{unreadCount, notifications: [{id, notifyType, title, keyword, announcementId, isRead, createdAt}, ...]}` (최신순 최대 50건). `notifyType`은 "신규매칭" | "마감임박". 이 테이블(`notification_logs`)에 실제로 알림을 쌓는 자동화 로직(수집→매칭→알림 생성, 이메일 발송)은 별도 작업이며 이번 범위는 저장된 알림의 조회/읽음 처리만 다룬다.
- `POST /api/v1/notifications/{id}/read` (로그인 필요) → 알림 1건 읽음 처리 (남의 알림/없는 id는 404 `NOTIFICATION_NOT_FOUND`)
- `POST /api/v1/notifications/read-all` (로그인 필요) → 내 알림 전체 읽음 처리 (FE `AlertsDropdown.tsx`의 "모두 읽음" 버튼용)

## Postman 문서화

`back/postman/Forward_BE_API.postman_collection.json`에 전체 엔드포인트를 Postman 컬렉션으로 정리해뒀습니다 (마이페이지 `/me`, 알림 `/notifications` 등 이 문서 작성 시점 기준 아직 머지 전인 PR의 엔드포인트도 포함 — 해당 PR들이 머지되면 바로 맞습니다).

사용법:
1. Postman에서 File → Import → 이 JSON 파일 선택
2. 컬렉션 변수 `baseUrl`을 서버 주소로 맞추기 (기본값 `http://localhost:8000/api/v1`)
3. `Auth (인증)` 폴더의 "로그인" 요청을 먼저 실행 — 응답의 `token`이 컬렉션 변수 `token`에 자동 저장되고, 로그인이 필요한 다른 요청들이 이 값을 `Authorization: Bearer` 헤더로 자동으로 씀
4. 관리자 전용 요청(`Admin`, `Collect`)은 관리자 계정으로 로그인해야 정상 동작 (`scripts/promote_admin.py`로 최초 관리자 지정)

각 요청의 Description에 성공/실패 응답 형태와 에러 코드를 적어뒀습니다.

## 수집 대상 (공공데이터포털)

| 소스 | 서비스 | 상태 |
|---|---|---|
| `kstartup` | 창업진흥원 K-Startup 사업공고 | 연동 완료 |
| `narajangteo` | 조달청 나라장터 입찰공고정보 | 연동 완료 |
| `msit` | 과학기술정보통신부 사업공고 | 연동 완료 |
| ~~`mss`~~ | 중소벤처기업부 사업공고 | 보류 (오퍼레이션명 미확인, 제외됨) |

## 알림·이메일 발송 자동화 (5주차 우선순위 P1)

매일 자동 수집(기본 06:00, `COLLECT_CRON_HOUR`/`COLLECT_CRON_MINUTE`) 직후 `app/core/scheduler.py`가 이어서 실행하는 순서:

1. 공고 수집·저장 (기존)
2. `app/services/notifier.py`의 `generate_keyword_match_notifications` — 모든 사용자의 키워드로 공고 제목을 매칭해서 `notification_logs`에 알림 적재. `신규매칭`(키워드 매칭되는 모든 공고) + `마감임박`(그중 announcements.py와 동일 기준으로 마감임박인 것). `UNIQUE(user_id, announcement_id, notify_type)` + `INSERT IGNORE`로 매일 전체를 다시 계산해도 중복 알림이 안 쌓임.
3. `send_pending_notification_emails` — `emailed_at`이 비어있는 알림을 사용자별로 모아 이메일 1통으로 발송, 성공하면 `emailed_at` 채움.

**이메일 발송은 SMTP 설정이 있어야 실제로 동작합니다.** `.env`의 `SMTP_HOST`가 비어있으면(기본값) 이메일 발송 없이 로그만 남기고 넘어갑니다 — 알림 저장(2번)까지는 SMTP 설정 여부와 무관하게 정상 동작합니다. 어떤 이메일 서비스(SMTP 릴레이/Gmail/SendGrid 등)를 쓸지는 아직 팀에서 결정 전이라, 결정되면 `.env`에 `SMTP_HOST`/`SMTP_PORT`/`SMTP_USERNAME`/`SMTP_PASSWORD`/`SMTP_FROM_EMAIL`/`SMTP_USE_TLS` 값만 채우면 코드 수정 없이 발송이 시작됩니다 (`.env.example` 참고). 로컬 디버그 SMTP 서버(`python -m smtpd -c DebuggingServer -n localhost:1025`)로 실제 발송 경로까지 테스트 완료했습니다.

"저장한 공고 마감임박 알림" (사용자가 마이페이지에서 D-7/D-3/D-1 중 선택하는 것, `ALERT_SETTINGS`)은 이번 범위가 아니고 별도 작업입니다 — 이번 자동화는 키워드 매칭 기반 알림만 다룹니다.

## RLS 없음 — 주의

MySQL/MariaDB에는 Supabase의 RLS가 없습니다. 사용자별 데이터 접근 제어는 **API 코드의 `user_id` 필터에 전적으로 의존**합니다 (keywords/saved_announcements 라우터는 모든 조회·삭제에 `user_id` 조건, 타인 소유는 404). 개인화 테이블 쿼리를 추가할 때 `user_id` 조건 누락이 곧 데이터 유출이므로 리뷰 필수 체크 항목입니다. (`docs/be/6th_wk_DB전환.md` 2절)

## 로그 (5주차 우선순위 - 예외/로그 보강)

`app/core/logging_config.py`의 `setup_logging()`을 `main.py`가 앱 생성 전에 호출합니다. 이전에는 `logging.basicConfig()`를 아무도 호출하지 않아서 `scheduler.py`/`notifier.py`의 `logger.info(...)` 로그(자동 수집 결과, 알림 생성/발송 개수 등)가 실제로는 콘솔에 전혀 안 찍히고 있었습니다 — 이제 정상적으로 보입니다.

또한 `app/core/errors.py`의 처리 안 된 예외(500) 핸들러가 이제 `logger.exception(...)`으로 전체 스택트레이스를 남깁니다. 예전에는 500 에러가 나도 서버 콘솔에 아무 흔적이 없어서 원인 추적이 불가능했습니다.

## 테스트 (5주차 우선순위 - API 테스트 보강)

`back/tests/`에 pytest 기반 API 테스트가 있습니다 (health/auth/keywords/saved-announcements/admin/dashboard, 총 34개 케이스 — 정상 케이스뿐 아니라 401/403/404/409 같은 실패 케이스와, 다른 사용자의 데이터에 접근 못 하는지(RLS 없음에 대한 회귀 방지)도 검증).

```bash
.venv\Scripts\pip install -r requirements-dev.txt   # pytest 설치 (최초 1회)
.venv\Scripts\python -m pytest tests\ -v
```

**주의**: 이 테스트는 `.env`의 `DATABASE_URL`이 가리키는 DB의 `users`/`employees`/`announcements`/`keywords`/`saved_announcements` 테이블 내용을 각 테스트 전에 전부 지웁니다(`tests/conftest.py`의 `clean_db`). **로컬 개발용 DB에서만 실행하세요 — 운영/공유 DB에 대고 실행하면 안 됩니다.**

`/collect`(공공데이터포털 실제 API 호출)는 외부 서비스 의존성 때문에 이번 자동화 테스트 범위에서 제외했습니다 — 필요하면 이후 mock 처리해서 추가할 수 있습니다.

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
    scheduler.py         APScheduler — POST /collect 하루 1회 자동 실행
  db/
    session.py           SQLAlchemy 세션 (Depends(get_db)). mysql일 때 세션 time_zone=UTC 고정
    models.py             ORM 모델 5개 (employees/users/announcements/keywords/saved_announcements)
  services/
    collector.py          공공데이터포털 API 3종 호출 + 필드 정규화
    storage.py             수집 결과를 announcements 테이블에 upsert (INSERT ... ON DUPLICATE KEY UPDATE)
  api/v1/
    router.py             라우터 모음
    health.py              헬스체크 (/health, /health/db)
    collect.py              수집 트리거 (GET: 미리보기, POST: 저장)
    announcements.py        저장된 공고 재조회 (검색/필터/정렬/페이지네이션)
    auth.py                 사원 인증 + 회원가입/로그인/로그아웃 (JWT)
    keywords.py             키워드 CRUD (로그인 필요)
    saved_announcements.py   공고 저장/저장취소/조회 (로그인 필요)
alembic/                 DB 마이그레이션 (스키마 정본). alembic/versions/*.py
alembic.ini
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

# DB 준비 (MySQL 8 / MariaDB 10.4+)
#   1) 빈 데이터베이스 + 계정 생성 (아래 SQL을 mysql -u root -p 로 1회 실행)
#        create database forward default character set utf8mb4 collate utf8mb4_unicode_ci;
#        create user if not exists 'forward'@'localhost' identified by 'forward';
#        grant all privileges on forward.* to 'forward'@'localhost';  -- 로컬은 마이그레이션까지 이 계정으로
#        flush privileges;
#   2) 스키마 적용
.venv\Scripts\alembic upgrade head
#   3) (선택) 데모 사원 시드
#        mysql -u root -p forward < dev-seed.sql

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

## 수집 대상 (공공데이터포털)

| 소스 | 서비스 | 상태 |
|---|---|---|
| `kstartup` | 창업진흥원 K-Startup 사업공고 | 연동 완료 |
| `narajangteo` | 조달청 나라장터 입찰공고정보 | 연동 완료 |
| `msit` | 과학기술정보통신부 사업공고 | 연동 완료 |
| ~~`mss`~~ | 중소벤처기업부 사업공고 | 보류 (오퍼레이션명 미확인, 제외됨) |

## RLS 없음 — 주의

MySQL/MariaDB에는 Supabase의 RLS가 없습니다. 사용자별 데이터 접근 제어는 **API 코드의 `user_id` 필터에 전적으로 의존**합니다 (keywords/saved_announcements 라우터는 모든 조회·삭제에 `user_id` 조건, 타인 소유는 404). 개인화 테이블 쿼리를 추가할 때 `user_id` 조건 누락이 곧 데이터 유출이므로 리뷰 필수 체크 항목입니다. (`docs/be/6th_wk_DB전환.md` 2절)

# 6주차 — DB 전환: Supabase(Postgres) → MySQL/MariaDB

> 작성일 2026-08-31 · 대상 코드: `back/`
> 단순 접속정보 교체가 아니라 Postgres 전용 코드가 여러 곳에 있어, 아래 지점을 전부 수정했습니다.

## 1. 변경 요약 (사전 확인된 지점 전부 반영)

| 위치 | 이전 (Postgres 전용) | 변경 후 (MySQL/MariaDB) |
|---|---|---|
| `back/app/db/models.py` 전 테이블 PK/FK | `postgresql.UUID` + `server_default=gen_random_uuid()` | `String(36)`(CHAR(36)) + 앱 생성 `default=str(uuid.uuid4())` |
| `back/app/db/models.py` 문자열 컬럼 | 전부 `Text` | PK/UNIQUE/FK 대상은 `String(n)`(VARCHAR) — MySQL은 TEXT에 인덱스 제한 |
| `back/app/db/models.py` 시간 컬럼 | `DateTime(timezone=True)` (timestamptz) | `DateTime` + **UTC 저장 규칙** (아래 3절) |
| `back/app/services/storage.py` | `postgresql.insert().on_conflict_do_update()` | `mysql.insert().on_duplicate_key_update()` (id는 앱에서 uuid 생성) |
| `back/app/api/v1/announcements.py` | `nulls_last()` 정렬, `func.current_date()+timedelta` | `(컬럼 IS NULL) ASC` 선행 정렬, 앱의 `date.today()` 리터럴 바인딩 — 둘 다 MySQL에 해당 문법/연산 없음 |
| `back/app/api/v1/auth·keywords·saved_announcements.py` | `uuid.UUID(...)` 객체로 PK 조회 | `str(uuid.UUID(...))` — 형식 검증 후 문자열로 조회 |
| `back/requirements.txt` | `psycopg2-binary` | `PyMySQL` + `cryptography`(MySQL 8 caching_sha2_password 인증용) |
| `back/.env(.example)`, `config.py` | `postgresql+psycopg2://...` | `mysql+pymysql://user:pw@host:3306/forward?charset=utf8mb4` |
| `back/supabase/*.sql` | Postgres DDL | 삭제. 스키마 정본은 **alembic** (`back/alembic/versions/`) — `docs/be/alembic-마이그레이션.md` |
| `back/app/db/session.py` | — | mysql URL일 때 세션 `time_zone='+00:00'` 고정 추가 |

> 7주차 갱신: 최초엔 `back/mysql/schema.sql` 단일 파일로 스키마를 만들었으나,
> 컬럼 추가 시 팀원이 DB를 통째로 다시 만들어야 하는 문제가 있어 **alembic 마이그레이션**으로 대체했습니다.
> `schema.sql`은 삭제됐고, 아래 4절 절차도 alembic 기준으로 갱신했습니다.

## 2. RLS 관련 팀 공지 ⚠️

MySQL/MariaDB에는 Supabase의 RLS(Row Level Security)가 **없습니다**.
이제 사용자별 데이터 접근 제어는 **API 코드의 `WHERE user_id == 로그인사용자` 필터에 전적으로 의존**합니다.

- 이미 keywords/saved_announcements 라우터는 모든 조회·삭제에 `user_id` 필터가 걸려 있고, 타인 소유는 404로 응답합니다 (소유권 노출 방지).
- **앞으로 개인화 테이블을 다루는 쿼리를 추가할 때 `user_id` 조건을 빠뜨리면 그대로 데이터가 새는 구조**이므로, 코드 리뷰 시 필수 체크 항목으로 삼아야 합니다.
- DB 계정 권한 최소화 권장: 앱 계정에는 forward DB의 DML만 부여 (아래 4절 계정 생성 참고).

## 3. 시간(UTC) 저장 규칙

- MySQL DATETIME은 시간대 정보가 없으므로, `session.py`가 연결마다 `SET time_zone='+00:00'`을 실행해 `CURRENT_TIMESTAMP`(created_at, collected_at, saved_at)가 **항상 UTC로 저장**되게 했습니다.
- 화면 표시용 KST 변환은 FE(또는 응답 계층)에서 처리합니다.
- 접수시작/마감일은 시간대 개념이 없는 `DATE`라 영향 없습니다. statusLabel/dday 계산은 앱 서버의 `date.today()`(KST) 기준입니다.

## 4. 로컬 개발 DB 준비 (alembic 기준)

```bash
# 1) MySQL 8 (또는 MariaDB 10.4+) 설치 후 빈 DB + 계정 생성
mysql -u root -p -e "
  create database if not exists forward
    default character set utf8mb4 collate utf8mb4_unicode_ci;
  create user if not exists 'forward'@'localhost' identified by 'forward';
  grant all privileges on forward.* to 'forward'@'localhost';
  flush privileges;"
# ↑ 로컬은 alembic(스키마 생성)도 이 계정으로 돌리므로 ALL. 공용/운영은 5절 참고.

# 2) back/.env
# DATABASE_URL=mysql+pymysql://forward:forward@localhost:3306/forward?charset=utf8mb4

# 3) 의존성 설치 + 스키마 적용
cd back && pip install -r requirements.txt
alembic upgrade head

# 4) (선택) 데모 사원 시드 — 프론트 회원가입 데모값(20230001 / 김민준)
mysql -u root -p forward < dev-seed.sql

# 5) 실행
uvicorn app.main:app --reload --port 8000
```

이후 스키마가 바뀌면 (팀원이 마이그레이션을 추가하면) pull 후 `alembic upgrade head` 한 줄로 동기화됩니다.
마이그레이션 추가/적용/롤백 절차는 **`docs/be/alembic-마이그레이션.md`**.

Docker를 쓰는 팀원은 (권장 — 팀 전원 동일 환경):

```bash
cd back && docker compose up -d --wait   # back/docker-compose.yml — DB·계정 자동 생성, healthy까지 대기
alembic upgrade head
```

위 1)의 SQL은 전부 생략됩니다 (compose가 forward DB와 forward 계정을 자동 생성).
처음이라면 **`docs/온보딩-MySQL과-Docker.md`** (1학년 눈높이 개념 설명 + 따라하기 + FAQ) 참고.

## 5. 데이터 이관

기존 Supabase의 실데이터가 적어(공고는 수집으로 재생성 가능) **별도 이관 스크립트 없이 재수집으로 재생성**합니다:

1. `alembic upgrade head` 로 스키마 생성 (+ 선택: `dev-seed.sql`로 데모 사원 — 실명부로 교체 필요)
2. 공공데이터포털 키 설정 후 `POST /api/v1/collect` 1회 실행 → announcements 재적재
3. 계정/키워드/저장공고는 테스트 데이터였으므로 재가입으로 대체

## 6. 스모크 테스트 결과 (2026-08-31, 로컬 MySQL 5.7 기준)

> 실행 환경: 로컬 mysqld 5.7.24 (port 3307) + venv(Python 3.11) + uvicorn
> ⚠️ MySQL 5.7은 CHECK 제약을 파싱만 하고 무시함 — 운영은 8.0+/MariaDB 10.4+ 권장 (앱 검증이 있어 동작엔 문제 없음)

| # | 확인 항목 | 결과 |
|---|---|---|
| 1 | `GET /health` | ✅ `{"status":"ok"}` |
| 2 | `GET /health/db` — MySQL 연결 | ✅ `{"db":"connected"}` |
| 3 | `POST /auth/verify-employee` 시드 사원 매칭 (있음 true / 없음 false) | ✅ |
| 4 | `POST /auth/signup` → users에 CHAR(36) uuid로 저장, 중복 사번 409 | ✅ `DUPLICATE_EMP_ID` |
| 5 | `POST /auth/login` → JWT 발급, 오입력 401 | ✅ `INVALID_CREDENTIALS` |
| 6 | `GET/POST/DELETE /keywords` (+중복 409, 무토큰 401) | ✅ 전부 정상 |
| 7 | `GET /announcements` 검색(q)·statusLabel 필터·deadline/latest 정렬 | ✅ 마감임박(dday≤3) 계산 포함 |
| 8 | `GET /announcements/{id}` + 존재하지 않는 id 404 | ✅ |
| 9 | `GET/POST/DELETE /saved-announcements` (+중복 409 `ALREADY_SAVED`) | ✅ |
| 10 | upsert 중복 방지 — 같은 (source, external_id) 재수집 시 3건 유지·제목만 갱신 | ✅ `on_duplicate_key_update` 동작 확인 |
| 11 | 접수기간 없는 공고(msit류) — 정렬 시 항상 맨 뒤, statusLabel/dday null | ✅ MySQL에서 NULLS LAST 대체 로직 정상 |
| 12 | created_at UTC 저장 (KST 08:45 → 23:45 UTC 기록 확인) | ✅ 세션 time_zone 고정 동작 |
| 13 | Postgres 전용 import 잔존 없음 (`grep dialects.postgresql`) | ✅ 없음 |

발견해서 함께 수정한 것:
- `schema.sql`에 `set names utf8mb4` 추가 — 클라이언트 기본 charset이 latin1이면 한글 시드가 깨져 사원 인증이 실패함 (실측으로 확인)
- 테스트 시 이메일 도메인으로 `*.test`를 쓰면 pydantic `EmailStr`(email-validator)이 특수용도 TLD라 422로 거부함 — `example.com` 등 사용

## 7. 완료 기준 체크리스트

- [x] `back/.env`의 `DATABASE_URL`이 MySQL/MariaDB를 가리키고 `GET /api/v1/health/db` 정상 응답 (로컬 MySQL 5.7 검증)
- [x] 기존 13개 엔드포인트 전체가 새 DB 기준으로 정상 동작 — collect 2종은 공공데이터포털 키가 없어 실호출 제외, 대신 동일 저장 경로(`save_announcements`)로 upsert 검증
- [x] Postgres 전용 import(`sqlalchemy.dialects.postgresql.*`)가 코드에 남아있지 않음

> 각자 로컬에서는 MySQL 8 / MariaDB 기준으로 4절 절차만 따라 하면 됩니다.

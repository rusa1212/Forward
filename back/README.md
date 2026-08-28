# forward-be

FastAPI 백엔드. 공공데이터포털 API로 공고 데이터를 수집해서 Supabase(Postgres)에 저장합니다.

## 폴더 구조

```
app/
  main.py              FastAPI 진입점, CORS 등록
  core/
    config.py           .env 읽는 설정값 (Settings)
  db/
    session.py           SQLAlchemy 세션 (Depends(get_db))
    models.py             Announcement ORM 모델 (Supabase의 실제 announcements 테이블과 1:1)
  services/
    collector.py          공공데이터포털 API 3종 호출 + 필드 정규화
    storage.py             수집 결과를 announcements 테이블에 upsert
  api/v1/
    router.py             라우터 모음
    health.py              헬스체크 (/health, /health/db)
    collect.py              수집 트리거 (GET: 미리보기, POST: 저장)
    announcements.py        저장된 공고 재조회
    auth.py                 사원 인증 + 회원가입/로그인/로그아웃 (JWT)
    keywords.py              키워드 등록/조회/삭제 (로그인 필요)
  core/
    errors.py             공통 오류 응답 형식 ({"success": false, "error": {...}})
requirements.txt
.env.example
supabase/
  employees_users.sql     Supabase SQL Editor에서 실행할 employees/users 테이블 생성 스크립트
  keywords.sql             Supabase SQL Editor에서 실행할 keywords 테이블 생성 스크립트
```

## 실행 방법

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS/Linux

copy .env.example .env   # DATA_GO_KR_API_KEY, DATABASE_URL, JWT_SECRET 채우기
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

`.env`에는 `DATABASE_URL`만 채우면 됩니다 (Supabase 프로젝트 > Database > Connection string에서 복사, `postgresql://`를 `postgresql+psycopg2://`로 바꿔서 사용). Supabase의 anon key / service_role key는 이 백엔드에서 쓰지 않습니다 — 서버가 `DATABASE_URL`로 Postgres에 직접 붙어서 처리하기 때문입니다.

Supabase 쪽에는 `supabase/employees_users.sql` 내용을 SQL Editor에 붙여넣고 한 번 실행해서 `employees`/`users` 테이블을 만들어야 회원가입/로그인이 동작합니다.

## 확인된 엔드포인트

- `GET /api/v1/health` → 서버 상태
- `GET /api/v1/health/db` → Supabase 연결 확인
- `GET /api/v1/collect` → 3개 소스(K-Startup, 나라장터, 과기정통부) 수집 미리보기 (DB 저장 안 함)
- `POST /api/v1/collect` → 수집 후 `announcements` 테이블에 upsert (`source`+`external_id` 기준 중복 방지)
- `GET /api/v1/announcements?limit=20&source=kstartup` → 저장된 공고 재조회
- `POST /api/v1/auth/verify-employee` → `{empId, name}`이 사원 명부와 일치하는지 확인 (회원가입 1단계)
- `POST /api/v1/auth/signup` → `{empId, name, email, pw}`로 계정 생성 (회원가입 2단계, 사원 인증 재검증)
- `POST /api/v1/auth/login` → `{empId, pw}` 검증 후 로그인 토큰(JWT) 발급
- `POST /api/v1/auth/logout` → 상태 없는(stateless) JWT라 서버가 지울 게 없음 (FE가 토큰만 버리면 됨)
- `GET /api/v1/keywords` (로그인 필요, 헤더 `Authorization: Bearer <token>`) → 내 키워드 목록
- `POST /api/v1/keywords` (로그인 필요) → `{keyword}`로 키워드 등록 (공백/50자 초과/중복 차단)
- `DELETE /api/v1/keywords/{id}` (로그인 필요) → 내 키워드 삭제 (다른 사람 키워드는 404)

## 수집 대상 (공공데이터포털)

| 소스 | 서비스 | 상태 |
|---|---|---|
| `kstartup` | 창업진흥원 K-Startup 사업공고 | 연동 완료 |
| `narajangteo` | 조달청 나라장터 입찰공고정보 | 연동 완료 |
| `msit` | 과학기술정보통신부 사업공고 | 연동 완료 |
| ~~`mss`~~ | 중소벤처기업부 사업공고 | 보류 (오퍼레이션명 미확인, 제외됨) |

## 다음에 할 일

- APScheduler로 `POST /api/v1/collect`를 하루 1회 자동 실행 (완료 — `core/scheduler.py`)
- 인증(JWT) — 완료 (`api/v1/auth.py`)
- 키워드 CRUD — 완료 (`api/v1/keywords.py`)
- 남은 것: 공고 검색/필터/정렬/페이지네이션, 저장공고 CRUD, 알림

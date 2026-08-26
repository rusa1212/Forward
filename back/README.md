# forward-be — WBS 1.1 스캐폴드

FastAPI 백엔드 프로젝트 기본 틀입니다. 실제로 로컬에서 띄우고 아래 항목까지 검증했습니다.

- 서버 실행 및 헬스체크 응답
- DB(PostgreSQL) 연결 확인
- 공통 에러 응답 형식 (`{"success": false, "error": {"code", "message"}}`) — 404/검증 에러/서버 에러 전부 동일한 형태로 통일
- FE(React, `localhost:3000`) 기준 CORS 허용
- Alembic 마이그레이션 (DB 팀원이 준 스키마와 100% 일치 확인됨)

## 폴더 구조

```
app/
  main.py            FastAPI 진입점, CORS/에러핸들러 등록
  core/
    config.py         .env 읽는 설정값 (Settings)
    errors.py          공통 에러 응답 구조
  db/
    session.py         SQLAlchemy 세션 (Depends(get_db)로 라우터에서 사용)
    models.py           DB 팀원이 설계한 ORM 모델 (7개 테이블)
  api/v1/
    router.py           라우터 모음 (앞으로 만들 기능별 라우터를 여기 등록)
    health.py            헬스체크 (/api/v1/health, /api/v1/health/db)
migrations/            Alembic (models.py 기준으로 자동 생성됨)
requirements.txt
.env.example
```

## 실행 방법

```bash
pip install -r requirements.txt
cp .env.example .env   # DB 팀원에게 받은 DATABASE_URL로 값 교체
uvicorn app.main:app --reload --port 8000
```

확인:
- `GET http://localhost:8000/api/v1/health` → `{"success": true, "data": {"status": "ok"}}`
- `GET http://localhost:8000/api/v1/health/db` → DB 연결 확인 (DATABASE_URL이 맞으면 success:true)

## 다음에 할 일 (WBS 순서)

1. **2.1 공고 수집 — 외부 API 호출**: `app/api/v1/` 옆에 `app/services/collector.py` 같은 파일 만들어서 NTIS/공공데이터 API 호출 로직 작성
2. **5.1/5.2 인증**: `app/api/v1/auth.py` 라우터 추가, `passlib`로 비밀번호 해시, `python-jose`로 JWT 발급 — `app.db.models.User`/`Employee` 그대로 사용
3. **3.1/3.2 공고 조회 API**: `app/api/v1/announcements.py` — `app.db.models.Announcement` 조회, `router.py`에 등록

새 라우터를 만들 때마다 `app/api/v1/router.py`에 `api_router.include_router(...)` 한 줄만 추가하면 됩니다.

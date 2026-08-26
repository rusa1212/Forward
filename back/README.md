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
requirements.txt
.env.example
```

## 실행 방법

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS/Linux

copy .env.example .env   # DATA_GO_KR_API_KEY, DATABASE_URL 채우기
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

## 확인된 엔드포인트

- `GET /api/v1/health` → 서버 상태
- `GET /api/v1/health/db` → Supabase 연결 확인
- `GET /api/v1/collect` → 3개 소스(K-Startup, 나라장터, 과기정통부) 수집 미리보기 (DB 저장 안 함)
- `POST /api/v1/collect` → 수집 후 `announcements` 테이블에 upsert (`source`+`external_id` 기준 중복 방지)
- `GET /api/v1/announcements?limit=20&source=kstartup` → 저장된 공고 재조회

## 수집 대상 (공공데이터포털)

| 소스 | 서비스 | 상태 |
|---|---|---|
| `kstartup` | 창업진흥원 K-Startup 사업공고 | 연동 완료 |
| `narajangteo` | 조달청 나라장터 입찰공고정보 | 연동 완료 |
| `msit` | 과학기술정보통신부 사업공고 | 연동 완료 |
| ~~`mss`~~ | 중소벤처기업부 사업공고 | 보류 (오퍼레이션명 미확인, 제외됨) |

## 다음에 할 일

- APScheduler로 `POST /api/v1/collect`를 하루 1회 자동 실행
- 5주차 항목: 인증(JWT), 조회/검색, 개인화, 대시보드, 알림

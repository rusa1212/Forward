# 4주차 BE 구현 정리 (2026-08-26)

> `docs/4th_wk_BE`에 정리된 4.4~4.6 작업을 `back/`에서 FastAPI + Supabase로 실제 구현한 내역입니다.

## 결과 요약

| WBS | 작업 | 상태 |
|---|---|---|
| 4.4 | Supabase 연결 | 완료 — `GET /api/v1/health/db`로 확인 |
| 4.5 | 외부 API 호출 | 완료 (3/4 소스) |
| 4.6 | DB 저장 | 완료 — upsert + 재조회 확인 |
| - | 하루 1회 자동 수집 | 완료 — APScheduler |

## 폴더 구조 (`back/`)

```
app/
  main.py                 FastAPI 진입점, CORS, 스케줄러 lifespan 연결
  core/
    config.py               .env 설정값
    scheduler.py             APScheduler (매일 자동 수집)
  db/
    models.py                Announcement ORM (Supabase 실제 테이블과 1:1)
    session.py                SQLAlchemy 세션 (Depends(get_db))
  services/
    collector.py              공공데이터포털 API 3종 호출 + 필드 정규화
    storage.py                  정규화 결과를 announcements 테이블에 upsert
  api/v1/
    router.py, health.py, collect.py, announcements.py
```

## 외부 API 연동 현황

공공데이터포털에서 발급받은 API 키(디코딩 키, `DATA_GO_KR_API_KEY`) 하나를 4개 서비스가 공용으로 사용.

| source | 서비스 | 오퍼레이션 | 비고 |
|---|---|---|---|
| `kstartup` | 창업진흥원 K-Startup 사업공고 | `getAnnouncementInformation01` | 응답이 XML `<col name="...">` 구조 |
| `narajangteo` | 조달청 나라장터 입찰공고정보 | `getBidPblancListInfoServc` | 조회 기간(`inqryBgnDt`/`inqryEndDt`) 필수 |
| `msit` | 과학기술정보통신부 사업공고 | `businessAnnouncMentList` | 파라미터명이 `ServiceKey`(대문자 S) |
| ~~`mss`~~ | 중소벤처기업부 사업공고 (`mssBizService_v2`) | 미확인 | data.go.kr 상세 스펙이 JS(Swagger)로만 렌더링되어 오퍼레이션명을 못 찾음 — 이번 범위에서 제외 |

## DB 스키마 (Supabase, 이미 존재하던 테이블)

`announcements` 테이블: `id(uuid pk)`, `source`, `external_id`, `title`, `department`, `reception_start`, `reception_end`, `status`, `detail_url`, `summary`, `collected_at`. `(source, external_id)` unique — 재수집 시 upsert로 갱신.

수집 결과의 `agency`는 이 테이블에 별도 컬럼이 없어 `department`가 비어있을 때만 대신 채움.

## 엔드포인트

- `GET /api/v1/health`, `GET /api/v1/health/db`
- `GET /api/v1/collect` — 3개 소스 수집 미리보기 (DB 저장 안 함)
- `POST /api/v1/collect` — 수집 + `announcements` upsert
- `GET /api/v1/announcements?limit=&source=` — 저장된 공고 재조회

## 자동 수집 (APScheduler)

`app/core/scheduler.py` — `AsyncIOScheduler`로 매일 `COLLECT_CRON_HOUR:COLLECT_CRON_MINUTE`(기본 06:00, `.env`에서 조정)에 3개 소스 수집 + upsert. FastAPI `lifespan`에서 서버 기동 시 시작, 종료 시 정리.

## 테스트 결과

- `POST /api/v1/collect` 실행 → `kstartup 100 / narajangteo 100 / msit 10`, 총 210건 저장
- `GET /api/v1/announcements` 재조회 → 실제 한글 공고 제목 정상 확인
- 스케줄러 잡 등록 확인 (`daily_announcement_collect`, cron 06:00) + `run_daily_collect()` 직접 실행 테스트 통과

## 환경변수 (`back/.env`)

```
FRONTEND_ORIGIN=http://localhost:3000
ENV=local
DATA_GO_KR_API_KEY=
DATABASE_URL=postgresql+psycopg2://...
COLLECT_CRON_HOUR=6
COLLECT_CRON_MINUTE=0
```

## 다음 할 일

- 중기부 API 오퍼레이션명 확인되면 `collector.py`에 4번째 소스 추가
- 5주차: 인증(JWT), 공고 조회/검색, 개인화, 대시보드, 알림
- GitHub: `feat/be-init` → `main` PR

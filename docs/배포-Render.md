# 백엔드 배포 — Render (무료 플랜)

프론트는 Vercel, 백엔드는 Render에 올린다. **DB는 Render에 만들지 않는다** — 회사 클라우드로
이전할 예정이라 `DATABASE_URL` 환경변수 하나로 외부 DB에 붙는 구조로 두었다.

관련 파일: `render.yaml`(배포 설정), `back/Dockerfile`(이미지), `back/.dockerignore`

## 0. 먼저 알아야 할 것

**DB 없이는 서버가 뜨지 않는다.** `back/app/db/session.py`가 import 시점에 `create_engine()`을
호출하기 때문에, `DATABASE_URL`이 비어 있으면 FastAPI가 시작되기도 전에 죽는다.
회사 클라우드 DB가 준비되기 전까지는 임시 MySQL 주소라도 넣어둬야 한다.
(DB가 바뀌면 Render 대시보드에서 `DATABASE_URL` 값만 교체 → 재배포. 코드 수정 없음)

**무료 플랜은 15분 동안 요청이 없으면 서버가 내려간다.** 다음 요청이 오면 다시 뜨는데 약 1분
걸린다. 시연 직전에는 Starter($7/월)로 올리면 이 대기가 사라진다.

## 1. 배포하기

1. Render 대시보드 > **New > Blueprint** > 이 저장소 선택
2. `render.yaml`을 읽어 `forward-backend` 서비스가 잡힌다. 아래 값만 직접 입력:

   | 환경변수 | 값 |
   |---|---|
   | `DATABASE_URL` | `mysql+pymysql://계정:비번@호스트:3306/forward?charset=utf8mb4` |
   | `DATA_GO_KR_API_KEY` | 공공데이터포털 발급 키 |
   | `FRONTEND_ORIGIN` | 배포된 Vercel 주소 (쉼표로 여러 개 가능) |

   `JWT_SECRET`은 Render가 무작위로 만들어 고정하므로 건드리지 않는다.
3. Apply → 빌드(약 2~3분) 후 `https://forward-backend-xxxx.onrender.com` 주소가 발급된다.
4. 확인: `curl https://<주소>/api/v1/health` → `{"success":true,...}`
   DB 연결까지 보려면 `/api/v1/health/db`

마이그레이션(`alembic upgrade head`)은 컨테이너가 뜰 때마다 자동 실행된다
(`back/Dockerfile`의 `CMD`). Render의 pre-deploy 명령이 유료 전용이라 여기에 걸어둔 것.

## 2. 프론트(Vercel)와 연결

Vercel 환경변수에 아래를 넣는다 (`front/src/lib/api.ts`가 읽는 값):

```
VITE_API_BASE_URL=https://<Render 주소>/api/v1
```

반대로 Render의 `FRONTEND_ORIGIN`에는 Vercel 주소를 넣어야 CORS가 열린다. 양쪽이 서로를
가리켜야 하므로, 한쪽 주소가 바뀌면 반대쪽 환경변수도 같이 고쳐야 한다.

Vercel은 PR마다 프리뷰 주소가 달라서 운영 주소만 열어두면 프리뷰에서 API가 전부 막힌다.
프리뷰도 쓰려면 Render에 `FRONTEND_ORIGIN_REGEX`를 추가한다:

```
FRONTEND_ORIGIN_REGEX=https://forward-.*-<팀슬러그>\.vercel\.app
```

## 3. 시간대 주의

`COLLECT_CRON_HOURS`는 **서버 로컬 시간** 기준이다. Render 기본값은 UTC라 그대로 두면
`6,18` 설정이 한국 시간 15시·03시에 실행된다. `render.yaml`에 `TZ=Asia/Seoul`을 넣어
한국 시간으로 맞춰두었으니 이 값을 지우지 말 것.

## 4. 정기 수집 — 외부 cron 연결

무료 플랜에서는 서버가 잠들어 있는 동안 APScheduler가 돌지 않는다. 그래서 외부 cron이
전용 엔드포인트를 때려 수집을 돌린다.

```
POST https://<Render 주소>/api/v1/collect/cron
헤더: X-Cron-Token: <CRON_TOKEN 값>
```

하는 일은 스케줄러와 완전히 같다 — 수집 → 저장 → 키워드 매칭 → 알림 생성 → 메일 발송.
(절차가 갈리지 않도록 양쪽이 `app/services/collect_cycle.py`의 같은 함수를 쓴다.)

설정 순서:

1. Render 대시보드 > 서비스 > Environment 에서 `CRON_TOKEN` 값을 복사한다
   (`render.yaml`이 `generateValue: true`로 두어서 Render가 자동 생성해 둔다).
2. cron-job.org 같은 무료 cron 서비스에 작업 2개를 만든다:

   | | 시각(KST) | URL | 비고 |
   |---|---|---|---|
   | 깨우기 | 05:55, 17:55 | `GET /api/v1/health` | 잠든 서버를 미리 깨워둔다 |
   | 수집 | 06:00, 18:00 | `POST /api/v1/collect/cron` | 헤더에 `X-Cron-Token` 추가 |

   **깨우기 작업이 필요한 이유**: 무료 플랜은 잠든 상태에서 첫 요청이 오면 뜨는 데 1분쯤
   걸리는데, 무료 cron 서비스는 보통 30초에 연결을 끊는다. 수집 요청이 그대로 버려질 수
   있어서 5분 먼저 깨워둔다.

3. 확인: `curl -X POST https://<주소>/api/v1/collect/cron -H "X-Cron-Token: <토큰>"`
   → `{"success":true,"data":{"status":"accepted"}}`

응답은 즉시 202로 돌아오고 실제 수집은 백그라운드에서 돈다(수십 초 걸려서 동기로 처리하면
cron이 매번 타임아웃으로 실패 처리한다). **결과는 응답이 아니라 Render의 Logs 탭에서 본다** —
`collect cycle done: fetched=... saved=... notified=... emailed=...`

동작 참고:
- `CRON_TOKEN`이 비어 있으면 이 엔드포인트는 404다 (토큰을 안 정한 채 배포해도 구멍이
  생기지 않도록). 토큰은 HTTP 헤더로 나가므로 **영숫자만** 가능하다.
- 앞선 수집이 아직 돌고 있으면 `{"status":"already_running"}`을 주고 겹쳐 돌리지 않는다.
- 기존 관리자용 `POST /api/v1/collect`는 그대로 남아 있다 (수동 확인용, 관리자 JWT 필요).

## 5. 로컬에서 배포 이미지 그대로 돌려보기

```bash
cd back
docker build -t forward-backend .
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="mysql+pymysql://forward:forward@host.docker.internal:3306/forward?charset=utf8mb4" \
  -e TZ=Asia/Seoul \
  -e FRONTEND_ORIGIN="http://localhost:8443" \
  forward-backend
```

## 6. 회사 클라우드로 옮길 때

Render를 Docker로 구성한 이유가 이것이다 — `back/Dockerfile`이 매 배포마다 실제로 빌드되고
있으므로, 같은 이미지를 회사 클라우드(ECS/쿠버네티스 등)에 그대로 올리면 된다.

옮기는 게 좋은 시점은 **DB가 회사 클라우드로 들어가는 때**다. 사내 DB는 보통 IP 허용목록이나
VPC 안에 있는데, Render의 기본 아웃바운드 IP는 Render 고객들이 공유하는 주소라 허용받기
어렵다(전용 고정 IP는 별도 유료 애드온). 백엔드를 DB와 같은 클라우드에 두면 내부 통신이라
이 문제 자체가 없어진다.

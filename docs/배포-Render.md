# 백엔드 배포 — Render (무료 플랜)

프론트는 Vercel, 백엔드는 Render에 올린다. **DB는 Render에 만들지 않는다** — 회사 서버에
도커로 띄우고, Render의 백엔드가 `DATABASE_URL` 하나로 거기에 붙는다.

관련 파일: `render.yaml`(배포 설정), `back/Dockerfile`(이미지), `back/.dockerignore`,
`back/docker-compose.prod.yml`(회사 서버의 MySQL)

## 0. 먼저 알아야 할 것

**DB 없이 먼저 배포해도 된다.** `DATABASE_URL`을 비워두면 마이그레이션을 건너뛰고 서버만
뜬다. 이 상태에서 되는 것과 안 되는 것은 아래와 같다.

| | 상태 |
|---|---|
| 서버 기동, `/api/v1/health` | 정상 |
| 프론트 화면, 라우팅, CORS | 정상 |
| 로그인·회원가입·공고 조회 등 DB를 쓰는 요청 | 503 `DATABASE_NOT_CONFIGURED` |
| 자동 수집 | 시작하지 않음 (공공데이터 API만 헛호출하게 되므로 아예 안 건다) |

배포 경로와 주소를 먼저 확정해두고 싶을 때 쓰면 된다. DB가 준비되면 Render 대시보드에서
`DATABASE_URL`만 채우고 재배포하면, 그때 마이그레이션이 돌면서 정상화된다 —
**코드 수정도 재빌드도 필요 없다.**

**무료 플랜은 15분 동안 요청이 없으면 서버가 내려간다.** 다음 요청이 오면 다시 뜨는데 약 1분
걸린다. 시연 직전에는 Starter($7/월)로 올리면 이 대기가 사라진다.

## 1. 회사 서버에 MySQL 띄우기

(DB 없이 먼저 올려볼 거면 이 절은 건너뛰고 2번으로 간다.)

`back/docker-compose.prod.yml`을 쓴다. 로컬 개발용(`docker-compose.yml`)과 따로 둔 이유는,
개발용이 계정을 `forward/forward`로 하드코딩하고 3306을 전체 개방하기 때문이다 —
인터넷에 열린 3306은 자동 스캐너가 상시 두드리는 포트라 그대로 노출하면 바로 뚫린다.

```bash
# 회사 서버의 back/ 폴더에서
cat > .env.prod <<'ENV'
MYSQL_ROOT_PASSWORD=<길고 무작위>
MYSQL_PASSWORD=<길고 무작위 — 앱이 쓸 forward 계정 비밀번호>
ENV

docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
```

두 값은 반드시 채워야 한다 (비어 있으면 컨테이너가 뜨지 않도록 해뒀다).

**방화벽에서 3306을 Render 아웃바운드 IP로만 열 것.** Render 대시보드 > 서비스 > Connect 에
그 IP 목록이 있다. 이 IP는 Render 고객들이 공유하는 주소라 "Render에서 오는 트래픽"까지만
좁혀주는 것이지 우리 서비스만 통과시키는 게 아니다 — 그래서 비밀번호도 여전히 중요하다.

### DB 연결은 자동으로 암호화된다

prod compose는 `--require-secure-transport=ON`으로 평문 접속을 막는다. 인터넷을 지나는
연결이라 평문이면 계정과 데이터가 그대로 노출되기 때문이다.

앱 쪽에는 **아무 설정도 필요 없다.** PyMySQL은 서버가 TLS를 지원하면 알아서 TLS로 붙는다
(실제로 붙여서 `TLS_AES_256_GCM_SHA384`로 암호화되는 것을 확인했다). `DATABASE_URL`은
아래 평범한 형태 그대로 쓰면 된다.

```
mysql+pymysql://forward:<비밀번호>@<공인IP 또는 도메인>:3306/forward?charset=utf8mb4
```

⚠️ URL에 `ssl_disabled=false`를 붙이지 말 것. 문자열 `'false'`가 참으로 해석돼 TLS가 꺼지고,
서버가 평문을 거부하므로 접속 자체가 실패한다.

참고: 이 TLS는 암호화만 하고 서버 인증서를 검증하지는 않는다(MySQL이 자동 생성하는
self-signed 인증서라 호스트명이 맞지 않는다). 검증까지 하려면 실제 도메인으로 발급받은
인증서를 서버에 넣고 URL에 `ssl_ca=<CA 파일 경로>`를 추가해야 한다.

## 2. 배포하기

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

## 3. 프론트(Vercel)와 연결

프론트 배포 자체는 `docs/배포-Vercel.md`에 있다. 여기서는 백엔드와 맞물리는 부분만 본다.

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

## 4. 시간대 주의

`COLLECT_CRON_HOURS`는 **서버 로컬 시간** 기준이다. Render 기본값은 UTC라 그대로 두면
`6,18` 설정이 한국 시간 15시·03시에 실행된다. `render.yaml`에 `TZ=Asia/Seoul`을 넣어
한국 시간으로 맞춰두었으니 이 값을 지우지 말 것.

## 5. 정기 수집 — 외부 cron 연결

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

## 6. 로컬에서 배포 이미지 그대로 돌려보기

```bash
cd back
docker build -t forward-backend .
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="mysql+pymysql://forward:forward@host.docker.internal:3306/forward?charset=utf8mb4" \
  -e TZ=Asia/Seoul \
  -e FRONTEND_ORIGIN="http://localhost:8443" \
  forward-backend
```

## 7. 회사 클라우드로 옮길 때

Render를 Docker로 구성한 이유가 이것이다 — `back/Dockerfile`이 매 배포마다 실제로 빌드되고
있으므로, 같은 이미지를 회사 클라우드(ECS/쿠버네티스 등)에 그대로 올리면 된다.

옮기면 좋아지는 점은 **DB 연결이 내부 통신이 된다**는 것이다. 지금 구조는 DB가 회사 서버에
있고 백엔드는 Render에 있어서, 둘 사이 트래픽이 인터넷을 지난다. 그래서 3306을 밖으로
열어야 하고(방화벽으로 Render IP만 허용), 그 IP도 Render 고객들이 공유하는 주소라
"Render에서 오는 트래픽"까지만 좁혀진다.

백엔드를 DB와 같은 서버·같은 네트워크에 두면 3306을 아예 밖으로 열 필요가 없어진다.
`back/docker-compose.prod.yml`에서 `ports` 항목을 지우고 백엔드 컨테이너를 같은 compose에
합치면 된다 — 그러면 DB는 내부 네트워크에서만 보인다.

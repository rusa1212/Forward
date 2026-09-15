# 프론트 배포 — Vercel

백엔드는 Render에 따로 올린다 (`docs/배포-Render.md`). 이 문서는 프론트만 다룬다.

관련 파일: `vercel.json`(저장소 루트), `front/.env.example`

## 1. 왜 설정이 필요한가

두 가지 때문이다.

**모노레포다.** 이 저장소는 npm workspace라 `package-lock.json`이 루트에 있고, 실제 앱은
`front/`에 있다. 그래서 "루트에서 install → `front`를 빌드 → `front/dist`를 배포"라고
알려줘야 한다.

**SPA다.** `front/src/main.tsx`가 `BrowserRouter`를 쓰고 `/dashboard`, `/mypage/keywords`
같은 진짜 경로를 쓴다. 설정이 없으면 이런 주소로 **직접 접속했을 때 404**가 난다 (서버에
그런 파일이 없으니까). 링크를 타고 들어가는 건 되는데 새로고침하면 깨지는, 흔한 증상이다.

`vercel.json`이 둘 다 해결한다. 대시보드에서 따로 만질 설정은 환경변수 하나뿐이다.

```json
{
  "framework": "vite",
  "installCommand": "npm install",
  "buildCommand": "npm run build",
  "outputDirectory": "front/dist",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

`rewrites`가 모든 경로를 `index.html`로 보내지만 정적 파일은 멀쩡하다 — Vercel은 실제
파일이 있는지 먼저 확인하고, 없을 때만 rewrite를 적용한다. (`/assets/index-xxxx.js`는
그대로 서빙된다)

## 2. 배포하기

1. Vercel > **Add New > Project** > 이 저장소 선택
2. **Root Directory는 저장소 루트 그대로 둔다** (`front`로 바꾸지 말 것 — `vercel.json`이
   루트 기준으로 쓰여 있다). 빌드 설정도 건드릴 필요 없다.
3. **Environment Variables**에 아래를 추가한다:

   ```
   VITE_API_BASE_URL = https://<Render 주소>/api/v1
   ```

   끝에 `/api/v1`까지 포함해야 한다 — `front/src/lib/api.ts`가 이 뒤에 경로를 붙인다.
   빼먹으면 모든 API 호출이 404가 난다.
4. Deploy → `https://<프로젝트명>.vercel.app` 발급

## 3. 백엔드와 서로 연결하기

양쪽이 서로를 가리켜야 한다. 한쪽만 하면 화면은 뜨는데 API가 전부 실패한다.

| 어디에 | 무엇을 | 값 |
|---|---|---|
| Vercel | `VITE_API_BASE_URL` | `https://<Render 주소>/api/v1` |
| Render | `FRONTEND_ORIGIN` | `https://<Vercel 주소>` |

Render 쪽을 빼먹으면 브라우저 콘솔에 CORS 에러가 뜬다 (서버는 정상인데 브라우저가 막는 것).

**주소가 바뀌면 반대쪽도 같이 고쳐야 한다.** 그리고 `VITE_API_BASE_URL`은 빌드 시점에
번들 안에 문자열로 박히므로, 이 값을 바꿨으면 **재배포해야 반영된다** (환경변수만 저장하고
넘어가면 그대로다).

## 4. 프리뷰 배포까지 쓰려면

Vercel은 PR마다 `https://forward-<해시>-<팀>.vercel.app` 같은 주소를 새로 만든다. Render의
`FRONTEND_ORIGIN`에는 운영 주소만 들어 있으므로 프리뷰에서는 API가 전부 CORS로 막힌다.

프리뷰도 쓰려면 Render 환경변수에 정규식을 추가한다:

```
FRONTEND_ORIGIN_REGEX=https://forward-.*-<팀슬러그>\.vercel\.app
```

팀 슬러그는 실제 프리뷰 주소를 한 번 열어보고 그 패턴에 맞춰 적으면 된다.

## 5. 로컬에서 빌드 결과물 확인하기

개발 서버(`npm run dev`)가 아니라 **실제 배포될 결과물**을 확인하고 싶을 때:

```bash
npm run build
npm run preview   # http://localhost:8443
```

`/dashboard` 같은 주소로 직접 들어가 봐서 404가 안 나면 SPA 설정이 맞는 것이다.

## 6. Node 버전

루트 `package.json`의 `engines.node`가 `22.x`로 고정돼 있다(`.mise.toml`과 동일). Vercel의
기본 Node 버전은 시간이 지나면 올라가는데, 이 값이 있으면 빌드 환경이 어느 날 갑자기
바뀌는 일이 없다.

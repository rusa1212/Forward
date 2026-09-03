# MySQL과 Docker — 아무것도 몰라도 되는 가이드

> Forward 팀 온보딩 문서 · 2026-09-04
> 대상: MySQL도 Docker도 처음인 팀원. 개념 설명 → 왜 쓰는지 → 따라하기(약 20분) 순서입니다.

---

## 0. 한 줄 요약

우리 서비스의 모든 데이터(공고, 계정, 키워드, 저장공고)는 **MySQL**이라는 "데이터 창고 프로그램"에 저장됩니다. 이 창고를 팀원 모두가 **완전히 똑같은 상태로** 자기 컴퓨터에 켜기 위해 **Docker**라는 도구를 씁니다.

---

## 1. MySQL이 뭐야?

**엑셀을 떠올리면 됩니다.** 엑셀 파일 하나에 시트가 여러 장 있듯이, MySQL 안에는 **테이블**(표)이 여러 개 있습니다. 우리 프로젝트의 테이블은:

| 테이블 | 저장하는 것 |
|---|---|
| employees | 사원 명부 (회원가입 때 사번+이름 대조용) |
| users | 가입한 계정 (비밀번호는 암호화 저장) |
| announcements | 수집해온 공고들 |
| keywords | 사용자별 알림 키워드 |
| saved_announcements | 사용자가 즐겨찾기한 공고 |

그럼 엑셀이랑 뭐가 다르냐면:

1. **규칙을 강제합니다.** "같은 공고는 두 번 저장 금지", "없는 사용자의 키워드는 저장 금지" 같은 규칙을 테이블에 걸어두면 실수로도 어길 수 없습니다.
2. **프로그램이 말을 겁니다.** 사람이 마우스로 여는 게 아니라, 우리 백엔드(FastAPI)가 "제목에 AI 들어간 공고 줘"라고 **SQL이라는 언어로 질문**하면 답을 줍니다.
3. **동시에 여럿이 써도 안 깨집니다.** 여러 사용자가 동시에 저장/조회해도 데이터가 꼬이지 않게 설계된 프로그램입니다.

중요한 특징: MySQL은 **화면이 없는 프로그램**입니다. 켜져 있으면 컴퓨터 뒤편에서 조용히 돌아가고, 백엔드가 접속해서 씁니다. "켜져 있는지"는 아래에서 배울 명령(`docker compose ps`)으로 확인합니다.

> 참고: 원래 우리는 Supabase(남이 운영해주는 클라우드 DB)를 썼는데, 6주차에 MySQL로 전환했습니다. 그래서 이제 **DB가 각자 컴퓨터에 하나씩** 있습니다. 내 DB의 데이터는 팀원에게 자동으로 공유되지 않는 게 정상이에요! 공유되는 건 데이터가 아니라 **구조(스키마)**이고, 이건 git의 alembic 마이그레이션 파일로 맞춥니다.

---

## 2. Docker가 뭐야?

MySQL을 그냥 설치하면 컴퓨터마다 다른 일이 벌어집니다 — 버전이 다르고, Windows냐 Mac이냐에 따라 설치법이 다르고, 예전에 깔았던 게 남아서 충돌하고, 설정(특히 한글 인코딩!)이 제각각이 됩니다. 그 유명한 *"어? 제 컴퓨터에서는 되는데요…"* 가 여기서 나옵니다.

Docker는 **프로그램을 밀키트처럼 포장해서 어느 컴퓨터에서든 똑같이 실행해주는 도구**입니다. 비유 하나로 끝까지 갑니다:

- **이미지** = 밀키트. "MySQL 8.4 + 우리 팀 설정"이 통째로 포장된 것. 인터넷(Docker Hub)에서 받아옵니다.
- **컨테이너** = 밀키트를 조리해서 **먹고 있는 상태**, 즉 실행 중인 프로그램. 켜고(up) 끄고(down) 버리고 다시 만들 수 있습니다.
- **볼륨** = 냉장고에 따로 보관하는 반찬통. **데이터는 여기에** 담깁니다. 설거지(`down`)를 해도 반찬(데이터)은 냉장고에 남고, 냉장고 정리(`down -v`)를 해야 사라집니다. (반찬통도 Docker가 관리합니다 — 어디 있는지 몰라도 됨)

핵심은 이겁니다: **팀원 4명이 같은 이미지로 컨테이너를 켜면, 4명의 MySQL이 버전·설정까지 완전히 동일**합니다. Windows든 Mac이든요. 꼬이면 버리고 다시 켜면 3분 만에 새것이 됩니다.

우리는 명령을 일일이 치는 대신 **Docker Compose**를 씁니다 — 팀 설정(버전, 비밀번호, 포트, 한글 설정)을 `back/docker-compose.yml` 파일에 적어뒀고, 팀원은 `docker compose up -d` 한 줄만 치면 됩니다. 이 파일이 git에 있으니 전원이 자동으로 같은 설정을 씁니다.

### 왜 우리 팀이 Docker + MySQL?

| 문제 | Docker가 주는 해결 |
|---|---|
| 팀원마다 OS가 다름 (Windows/Mac) | 같은 이미지 = 같은 MySQL. 설치법 통일 |
| 한글 깨짐 사고 (utf8mb4 설정 누락) | compose 파일에 한글 설정이 박제되어 있어 잊을 수 없음 |
| DB 꼬였을 때 복구 | `down -v` → `up -d` 두 줄이면 공장초기화 |
| 신규 합류자 온보딩 | 이 문서 하나면 끝 |

---

## 3. 따라하기 (처음부터 끝까지, 약 20분)

> 📦 **준비물**: 터미널 여는 법만 알면 됩니다.
> Mac → `Cmd+Space` 눌러 Spotlight에 "터미널" 검색. Windows → 시작 메뉴에 "PowerShell" 검색.
>
> 📍 **위치 규칙**: 3-3부터의 모든 명령은 **`Forward/back` 폴더 안에서** 칩니다. 터미널을 새로 열었거나 재부팅했다면 `cd` 명령으로 다시 이동한 뒤 진행하세요. 지금 어디에 있는지 모르겠으면 `pwd`(Mac) / `Get-Location`(Windows)을 쳐보면 현재 폴더가 나옵니다.

### 3-1. 프로젝트 받기 (최초 1회)

git이 설치돼 있다면 (없으면 https://git-scm.com 에서 설치):

```bash
git clone https://github.com/rusa1212/Forward.git
```

```bash
cd Forward/back
```

이미 clone해둔 사람은 최신으로 갱신만: 프로젝트 폴더에서 `git pull` 후 `cd back`.

### 3-2. Docker Desktop 설치 (최초 1회)

- https://www.docker.com/products/docker-desktop/ 에서 다운로드
- **Windows**: 설치 중 "WSL 2" 관련 항목은 체크된 그대로. 재부팅을 요구하면 재부팅.
- **Mac**: 칩 종류(Apple Silicon / Intel)에 맞는 파일 선택 → dmg 열어서 설치.
- 설치 후 **Docker Desktop 앱을 실행**해 두세요. 고래 아이콘이 뜨고 "Engine running"이면 준비 끝.

**새 터미널 창을 열고** (설치 전에 열어둔 창은 docker 명령을 못 찾습니다) 확인:

```bash
docker --version
```

버전이 찍히면 성공입니다.

### 3-3. DB 켜기 (back/ 에서)

```bash
docker compose up -d
```

첫 실행은 이미지를 내려받느라 몇 분 걸립니다(다음부터는 몇 초). 끝나면:

```bash
docker compose ps
```

`STATUS`에 **healthy**가 보이면 MySQL이 켜진 겁니다. `starting`이면 30초쯤 기다렸다 다시 확인하세요. **healthy가 되기 전에는 다음 단계로 넘어가지 마세요.**

> 🚨 **"port is already allocated" 에러가 나면**: 컴퓨터에 MySQL을 직접 설치한 적이 있는 겁니다 (예: `brew install mysql`). 기존 것을 끄거나(Mac: `brew services stop mysql`), `docker-compose.yml`의 포트를 `"3307:3306"`으로 바꾸고 3-5의 `.env` 포트도 3307로 맞추세요.

### 3-4. Python 준비 (back/ 에서, 최초 1회)

백엔드 실행 도구(alembic, uvicorn)는 Python 패키지라서 설치가 필요합니다. 먼저 Python 3.11+ 확인 (`python --version` 또는 `python3 --version`, 없으면 https://www.python.org 에서 설치):

**venv**(이 프로젝트 전용 파이썬 도구 상자)를 만들고 패키지 설치 —

Windows (PowerShell):

```bash
python -m venv .venv
```

```bash
.venv\Scripts\pip install -r requirements.txt
```

Mac:

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

> 아래 3-6부터 Windows는 `.venv\Scripts\`, Mac은 `.venv/bin/`을 명령 앞에 붙입니다. "도구 상자에서 꺼내 쓴다"고 생각하면 됩니다. (venv "활성화"라는 방법도 있지만 Windows 기본 보안 정책에 막히는 경우가 있어, 이 문서는 경로를 직접 붙이는 방식으로 통일합니다.)

### 3-5. 백엔드 설정 파일 만들기 (back/ 에서)

`.env`는 **내 컴퓨터 전용 설정 파일**입니다 (git에 안 올라감 → 그래서 직접 만들어야 함). 견본을 복사해서 시작합니다:

Windows: `copy .env.example .env` · Mac: `cp .env.example .env`

VS Code 등 편집기로 `back/.env`를 열어 `DATABASE_URL=` 줄을 이렇게 채우세요:

```
DATABASE_URL=mysql+pymysql://forward:forward@localhost:3306/forward?charset=utf8mb4
```

`forward`라는 DB와 계정은 3-3에서 컨테이너가 **자동으로 만들어**뒀습니다. 참고로 계정은 두 개입니다 — **forward/forward**(백엔드가 쓰는 계정)와 **root/root**(사람이 관리용으로 쓰는 계정). 둘 다 compose가 자동 생성했습니다.

### 3-6. 테이블 만들기 + 데모 사원 넣기 (back/ 에서)

테이블 생성 (git에 있는 마이그레이션 파일들을 내 DB에 적용 — 앞으로 스키마가 바뀌어도 pull 후 이 한 줄이면 동기화):

Windows: `.venv\Scripts\alembic upgrade head` · Mac: `.venv/bin/alembic upgrade head`

`INFO ... Running upgrade` 줄들이 나오고 에러 없이 끝나면 성공입니다.

데모 사원(회원가입 테스트용 20230001/김민준) 넣기:

Mac:

```bash
docker exec -i forward-mysql mysql -uroot -proot --default-character-set=utf8mb4 forward < dev-seed.sql
```

Windows (PowerShell은 `<` 기호를 지원하지 않아 cmd로 감쌉니다):

```bash
cmd /c "docker exec -i forward-mysql mysql -uroot -proot --default-character-set=utf8mb4 forward < dev-seed.sql"
```

시드 명령은 **성공하면 아무것도 출력하지 않습니다** (에러가 없으면 성공). 진짜 들어갔는지 눈으로 확인:

```bash
docker exec -it forward-mysql mysql -uroot -proot --default-character-set=utf8mb4 forward -e "select * from employees;"
```

`20230001 | 김민준 | 개발팀` 한 줄이 보이면 성공입니다.

### 3-7. 서버 실행 + 최종 확인 (back/ 에서)

Windows: `.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000`
Mac: `.venv/bin/uvicorn app.main:app --reload --port 8000`

(uvicorn = 우리 백엔드 FastAPI를 실제로 켜주는 실행기입니다.)

이 명령은 **끝나지 않고 로그가 계속 흐르는 게 정상**입니다 — 서버가 켜져 있다는 뜻이니 터미널은 그대로 두세요. 끌 때는 그 터미널에서 `Ctrl+C`.

브라우저에서 http://localhost:8000/api/v1/health/db 를 열어 `{"success":true,"data":{"db":"connected"}}`가 나오면 **전부 성공**입니다. 🎉

---

## 4. 평소에 쓰는 명령 (이 5개면 충분)

`back/` 폴더에서:

| 명령 | 하는 일 |
|---|---|
| `docker compose up -d` | DB 켜기 (개발 시작할 때) |
| `docker compose ps` | 켜져 있나 확인 (healthy = 정상) |
| `docker compose logs db` | 에러 났을 때 DB 로그 보기 |
| `docker compose down` | DB 끄기 — **데이터는 남음** (설거지) |
| `docker compose down -v` | DB 끄고 **데이터까지 삭제** (냉장고 정리. 신중히!) |

DB 안을 눈으로 구경하고 싶으면:

```bash
docker exec -it forward-mysql mysql -uroot -proot --default-character-set=utf8mb4 forward
```

MySQL 대화창이 열립니다. `show tables;` (표 목록), `select * from employees;` (사원 명부), `exit` (나가기).

마우스로 보고 싶으면 무료 프로그램 **DBeaver**에 연결: 호스트 `localhost` · 포트 `3306` · 사용자 `forward` · 비밀번호 `forward` · 데이터베이스 `forward`.

---

## 5. 뭔가 안 될 때 (FAQ)

**Q. `docker: command not found` (명령을 찾을 수 없음)**
→ Docker 설치 **전에** 열어둔 터미널 창을 쓰고 있는 경우가 대부분입니다. **터미널 창을 새로 열어** 다시 시도하세요. 그래도 안 되면 Docker Desktop 재설치.

**Q. "Cannot connect to the Docker daemon" / "error during connect"**
→ Docker Desktop **앱이 꺼져 있는** 겁니다. 앱을 실행하고 고래 아이콘이 안정될 때까지 기다린 뒤 다시 시도하세요. (위의 command not found와는 다른 문제입니다)

**Q. `docker compose up`에서 "port is already allocated"**
→ 3306 포트를 다른 프로그램(대개 직접 설치한 MySQL)이 쓰는 중. 3-3의 🚨 참고.

**Q. Windows에서 WSL 관련 에러 창이 뜸**
→ PowerShell에서 `wsl --update` 실행 후 Docker Desktop 재시작. 그래도 안 되면 BIOS에서 가상화(VT-x/SVM) 활성화가 필요할 수 있습니다.

**Q. `alembic upgrade head`에서 접속 에러**
→ ① `docker compose ps`가 healthy인지 ② `.env`의 DATABASE_URL 오타/포트 확인. 이 두 개가 원인의 90%입니다.

**Q. `.venv\Scripts\activate`가 "스크립트 실행이 비활성화" 에러를 냄 (Windows)**
→ 이 문서 방식(경로 직접 붙이기)을 쓰면 활성화가 필요 없습니다. 굳이 활성화하려면 PowerShell에서 `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` 1회 실행.

**Q. 한글이 ???나 ê¹€ 같은 외계어로 보임**
→ compose 설정 덕에 서버는 안전하지만, mysql 명령으로 직접 넣을 때는 `--default-character-set=utf8mb4`를 꼭 붙이세요 (이 문서의 명령들엔 이미 붙어 있음).

**Q. DB를 완전히 처음 상태로 되돌리고 싶어**
→ `docker compose down -v` → `docker compose up -d` → (healthy 확인) → `alembic upgrade head` → 시드 다시 넣기. 3분 컷.

**Q. 내가 넣은 데이터가 팀원한테 안 보여요**
→ 정상입니다! DB는 각자 컴퓨터에 하나씩이에요 (1절 참고). 공유되는 건 구조(alembic)와 코드(git)입니다.

---

## 6. 용어 미니 사전

| 용어 | 뜻 |
|---|---|
| DB(데이터베이스) | 데이터를 규칙에 따라 저장·조회하는 창고 프로그램 |
| 테이블 | DB 안의 표 하나 (엑셀 시트 느낌) |
| SQL | DB에게 말 거는 언어 (`select * from ...`) |
| 이미지 | 프로그램+설정 밀키트 (다운로드 받는 것) |
| 컨테이너 | 이미지를 실행한 상태 (켜고 끄는 것) |
| 볼륨 | 데이터 보관함 — 컨테이너를 지워도(`down`) 데이터 유지, `down -v`로만 삭제 |
| 포트 | 프로그램의 문 번호. MySQL은 3306번 문을 씀 |
| docker compose | 팀 설정 파일(yml)대로 컨테이너를 켜주는 기능 |
| alembic | 테이블 구조 변경을 git으로 관리하는 도구 — `alembic upgrade head` 한 줄로 내 DB를 최신 구조로 |
| venv | 이 프로젝트 전용 파이썬 도구 상자 (컴퓨터의 다른 파이썬과 격리) |
| uvicorn | 우리 백엔드(FastAPI)를 실제로 켜주는 실행기 |
| .env | 내 컴퓨터 전용 설정 파일 — git에 안 올라가므로 각자 만들어야 함 |

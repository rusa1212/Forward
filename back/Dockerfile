# Forward 백엔드(FastAPI) 배포 이미지.
# Render가 이 파일로 빌드하고, 나중에 DB를 회사 클라우드로 옮길 때도 같은 이미지를 그대로 쓴다.
# 로컬 개발은 여전히 .venv + uvicorn 직접 실행이 편하다 (back/README.md).
FROM python:3.12-slim

# tzdata: APScheduler는 "서버 로컬 시간"으로 cron을 돌리는데(app/core/scheduler.py),
# slim 이미지엔 시간대 DB가 없어서 TZ=Asia/Seoul을 줘도 UTC로 동작한다. 그래서 직접 설치.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# requirements를 먼저 복사해야 소스만 바뀐 배포에서 pip 설치 레이어가 캐시된다.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# Render는 리슨할 포트를 $PORT로 넣어준다 (로컬에서 docker run 할 때는 8000).
# 마이그레이션을 여기서 돌리는 이유: Render의 pre-deploy 명령은 유료 플랜 전용이라
# 무료 플랜에선 컨테이너 시작 시점이 alembic을 걸 수 있는 유일한 지점이다.
#
# exec를 붙이는 이유: 이게 없으면 uvicorn이 sh의 자식 프로세스로 남아 Render가 재배포/중지 때
# 보내는 SIGTERM을 받지 못한다 → lifespan의 stop_scheduler()가 실행되지 않고 강제 종료된다.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

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

# 마이그레이션 실행과 서버 기동은 docker-entrypoint.sh 가 맡는다
# (DATABASE_URL이 비어 있으면 마이그레이션을 건너뛰고 DB 없이 뜬다 — 자세한 설명은 그 파일).
# COPY로 들어온 파일은 Windows에서 실행 비트가 없을 수 있어 여기서 붙여준다.
RUN chmod +x /app/docker-entrypoint.sh
CMD ["/app/docker-entrypoint.sh"]

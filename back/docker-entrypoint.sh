#!/bin/sh
# 컨테이너 시작 스크립트. Render의 pre-deploy 명령이 유료 플랜 전용이라
# 마이그레이션을 여기서 실행한다.
set -e

if [ -n "$DATABASE_URL" ]; then
  echo "[entrypoint] 마이그레이션 실행: alembic upgrade head"
  alembic upgrade head
else
  # DB를 아직 붙이지 않은 상태로도 배포할 수 있게 한다. 이 경우 서버는 뜨고
  # /api/v1/health 는 정상 응답하지만, DB를 쓰는 요청은 503으로 떨어진다.
  # DATABASE_URL을 채우고 재배포하면 이 자리에서 마이그레이션이 돌면서 정상화된다.
  echo "[entrypoint] DATABASE_URL이 비어 있어 마이그레이션을 건너뜁니다 (DB 없이 기동)."
fi

# exec: uvicorn이 PID 1이 되어 Render가 보내는 SIGTERM을 직접 받는다.
# 안 그러면 sh의 자식으로 남아 신호를 못 받고 강제 종료된다(lifespan 정리가 안 됨).
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

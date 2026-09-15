"""공고 자동 수집 스케줄. FastAPI lifespan에서 시작/종료됩니다.

기본은 하루 2회(06시·18시, `COLLECT_CRON_HOURS`). 한 번 실행될 때 수집 → 키워드 매칭 →
알림 생성 → (SMTP 설정 시) 이메일 발송까지 이어서 하므로, 키워드 매칭 공고는 다음 수집
실행 때(최대 반나절 내) 사용자에게 메일로 나간다. 발송 주기(daily/weekly)는 사용자별
alert_settings를 그대로 따른다 — daily면 매 실행마다, weekly면 월요일 실행에만.

실제로 무슨 일을 하는지는 app/services/collect_cycle.py에 있다 (외부 cron 경로와 공유).

⚠️ 배포 주의: 이 스케줄러는 서버 프로세스가 살아 있을 때만 돈다. Render 무료 플랜처럼
서버가 유휴 시 잠드는 환경에서는 정기 실행이 건너뛰어지므로, 외부 cron이
POST /api/v1/collect/cron 을 때리는 방식을 함께 쓴다 (docs/배포-Render.md).
"""
import logging
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.services.collect_cycle import run_collect_cycle

logger = logging.getLogger("app.scheduler")

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    # DB가 아직 연결되지 않은 상태로도 서버는 뜬다(app/db/session.py). 그때 수집을 돌리면
    # 공공데이터포털 API만 실컷 호출하고 저장 단계에서 매번 실패하므로 아예 걸지 않는다.
    if not settings.DATABASE_URL:
        logger.warning("DATABASE_URL이 비어 있어 자동 수집을 시작하지 않습니다.")
        return

    # trigger 없이 add_job하면 APScheduler가 "지금 바로 1회" 실행으로 예약한다.
    # 서버를 막 켰을 때 다음 정기 수집(06시/18시) 전까지 공고가 비어 보이는 문제 방지용.
    # pytest 하에서는 TestClient(app)이 매 테스트마다 lifespan을 실행하므로, 이 job이
    # 그대로 켜져 있으면 테스트마다 실제 공공데이터포털 API를 호출해 테스트 DB를 오염시킨다.
    if "pytest" not in sys.modules:
        scheduler.add_job(
            run_collect_cycle,
            id="startup_announcement_collect",
            replace_existing=True,
        )
    scheduler.add_job(
        run_collect_cycle,
        trigger=CronTrigger(hour=settings.COLLECT_CRON_HOURS, minute=settings.COLLECT_CRON_MINUTE),
        id="scheduled_announcement_collect",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "scheduler started: startup collect + collect at hours=[%s] minute=%02d",
        settings.COLLECT_CRON_HOURS,
        settings.COLLECT_CRON_MINUTE,
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)

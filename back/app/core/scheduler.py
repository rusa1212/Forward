"""공고 자동 수집. FastAPI lifespan에서 시작/종료됩니다.

기본은 하루 2회(06시·18시, `COLLECT_CRON_HOURS`). 각 실행마다 수집 직후 키워드 매칭 →
알림 생성 → (SMTP 설정 시) 이메일 발송까지 이어서 하므로, 키워드 매칭 공고는 다음 수집
실행 때(최대 반나절 내) 사용자에게 메일로 나간다. 발송 주기(daily/weekly)는 사용자별
alert_settings를 그대로 따른다 — daily면 매 실행마다, weekly면 월요일 실행에만.
"""
import logging
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.collector import collect_all, today_bid_date_range
from app.services.notifier import generate_keyword_match_notifications, send_pending_notification_emails
from app.services.storage import save_announcements

logger = logging.getLogger("app.scheduler")

scheduler = AsyncIOScheduler()


async def run_scheduled_collect() -> None:
    inqry_bgn_dt, inqry_end_dt = today_bid_date_range()
    result = await collect_all(inqry_bgn_dt, inqry_end_dt)
    all_items = [item for items in result.values() for item in items]

    db = SessionLocal()
    try:
        saved = save_announcements(db, all_items)
        # 수집 직후 키워드 매칭 → 알림 생성 → (SMTP 설정돼있으면) 이메일 발송까지 이어서 실행.
        # 이 실행이 하루 2회이므로, 새 매칭 공고는 반나절 안에 메일로 나간다.
        notified = generate_keyword_match_notifications(db)
        emailed = send_pending_notification_emails(db)
    finally:
        db.close()

    counts = {source: len(items) for source, items in result.items()}
    logger.info(
        "scheduled collect done: fetched=%s saved=%d notified=%d emailed=%d",
        counts, saved, notified, emailed,
    )


def start_scheduler() -> None:
    # trigger 없이 add_job하면 APScheduler가 "지금 바로 1회" 실행으로 예약한다.
    # 서버를 막 켰을 때 다음 정기 수집(06시/18시) 전까지 공고가 비어 보이는 문제 방지용.
    # pytest 하에서는 TestClient(app)이 매 테스트마다 lifespan을 실행하므로, 이 job이
    # 그대로 켜져 있으면 테스트마다 실제 공공데이터포털 API를 호출해 테스트 DB를 오염시킨다.
    if "pytest" not in sys.modules:
        scheduler.add_job(
            run_scheduled_collect,
            id="startup_announcement_collect",
            replace_existing=True,
        )
    scheduler.add_job(
        run_scheduled_collect,
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

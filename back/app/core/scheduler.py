"""하루 1회 공고 자동 수집. FastAPI lifespan에서 시작/종료됩니다."""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.collector import collect_all, today_bid_date_range
from app.services.storage import save_announcements

logger = logging.getLogger("app.scheduler")

scheduler = AsyncIOScheduler()


async def run_daily_collect() -> None:
    inqry_bgn_dt, inqry_end_dt = today_bid_date_range()
    result = await collect_all(inqry_bgn_dt, inqry_end_dt)
    all_items = [item for items in result.values() for item in items]

    db = SessionLocal()
    try:
        saved = save_announcements(db, all_items)
    finally:
        db.close()

    counts = {source: len(items) for source, items in result.items()}
    logger.info("daily collect done: fetched=%s saved=%d", counts, saved)


def start_scheduler() -> None:
    scheduler.add_job(
        run_daily_collect,
        trigger=CronTrigger(hour=settings.COLLECT_CRON_HOUR, minute=settings.COLLECT_CRON_MINUTE),
        id="daily_announcement_collect",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "scheduler started: daily collect at %02d:%02d",
        settings.COLLECT_CRON_HOUR,
        settings.COLLECT_CRON_MINUTE,
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)

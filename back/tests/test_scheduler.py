"""자동 수집 스케줄 설정 검증 (하루 2회)."""
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings


def test_collect_cron_default_is_twice_daily():
    assert settings.COLLECT_CRON_HOURS == "6,18"
    assert settings.COLLECT_CRON_MINUTE == 0


def test_cron_trigger_fires_at_configured_hours():
    """CronTrigger가 설정된 시각(기본 06·18시)에 하루 2번 발화하는지."""
    trigger = CronTrigger(
        hour=settings.COLLECT_CRON_HOURS,
        minute=settings.COLLECT_CRON_MINUTE,
        timezone="UTC",
    )
    prev = None
    now = datetime(2026, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC"))
    fires = []
    for _ in range(4):
        nxt = trigger.get_next_fire_time(prev, now)
        fires.append((nxt.day, nxt.hour, nxt.minute))
        prev = nxt
        now = nxt

    assert fires == [(1, 6, 0), (1, 18, 0), (2, 6, 0), (2, 18, 0)]

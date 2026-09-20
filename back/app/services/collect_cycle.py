"""수집 1회분의 전체 과정 — 수집 → 저장 → 오래된 마감 공고 정리 → 키워드 매칭 알림 생성 → 메일 발송.

호출하는 곳이 둘이다:
  - app/core/scheduler.py   : 서버가 깨어 있을 때 도는 정기 실행(06시·18시)
  - app/api/v1/collect.py   : 외부 cron이 때리는 POST /api/v1/collect/cron

두 경로가 각자 절차를 갖고 있으면 한쪽만 고쳐져서 "수집은 되는데 메일이 안 나간다" 같은
차이가 생긴다. 그래서 절차는 여기 한 곳에만 둔다.
"""
import logging

from app.db.session import SessionLocal
from app.services.collector import collect_all, today_bid_date_range
from app.services.notifier import generate_keyword_match_notifications, send_pending_notification_emails
from app.services.storage import purge_stale_closed_announcements, save_announcements

logger = logging.getLogger("app.collect_cycle")

# 실행 중 여부. 수집은 외부 API를 여러 번 호출해 수십 초가 걸릴 수 있어서, 정기 실행과
# cron 호출이 겹치면 같은 일을 두 번 하게 된다. 파이썬 asyncio는 단일 스레드라 이 플래그를
# 읽고 쓰는 사이에 다른 코루틴이 끼어들지 않으므로 별도 락 없이 이걸로 충분하다.
_running = False


def is_collect_running() -> bool:
    return _running


async def run_collect_cycle() -> dict:
    """수집 한 바퀴를 돌고 처리 건수를 돌려준다."""
    global _running
    _running = True
    try:
        inqry_bgn_dt, inqry_end_dt = today_bid_date_range()
        result = await collect_all(inqry_bgn_dt, inqry_end_dt)
        all_items = [item for items in result.values() for item in items]

        db = SessionLocal()
        try:
            saved = save_announcements(db, all_items)
            # 저장 직후에 정리한다 — 알림 생성(아래)이 보기 전에 지워야, 이미 보관 기간이
            # 지난 공고로 "신규매칭" 알림이 나가는 일이 없다.
            purged = purge_stale_closed_announcements(db)["deleted"]
            notified = generate_keyword_match_notifications(db)
            emailed = send_pending_notification_emails(db)
        finally:
            db.close()
    finally:
        _running = False

    summary = {
        "fetched": {source: len(items) for source, items in result.items()},
        "saved": saved,
        "purged": purged,
        "notified": notified,
        "emailed": emailed,
    }
    logger.info(
        "collect cycle done: fetched=%s saved=%d purged=%d notified=%d emailed=%d",
        summary["fetched"], saved, purged, notified, emailed,
    )
    return summary

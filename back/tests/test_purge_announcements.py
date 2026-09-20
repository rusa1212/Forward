"""보관 기간이 지난 마감 공고 정리 (app/services/storage.py의 purge_stale_closed_announcements)."""
import asyncio
import uuid
from datetime import date, timedelta

from sqlalchemy import select

from app.db.models import Announcement, NotificationLog, SavedAnnouncement
from app.services.collector import RECENT_CLOSED_DAYS
from app.services.storage import purge_stale_closed_announcements


def _add(db, external_id: str, reception_end: date | None) -> str:
    ann = Announcement(
        id=str(uuid.uuid4()),
        source="kstartup",
        external_id=external_id,
        title=f"공고 {external_id}",
        department="과기정통부",
        reception_start=date.today() - timedelta(days=200),
        reception_end=reception_end,
    )
    db.add(ann)
    db.commit()
    return ann.id


def _remaining(db) -> set[str]:
    return set(db.execute(select(Announcement.external_id)).scalars().all())


def test_deletes_only_long_closed(db):
    today = date.today()
    _add(db, "old", today - timedelta(days=RECENT_CLOSED_DAYS + 1))
    _add(db, "recent-closed", today - timedelta(days=RECENT_CLOSED_DAYS - 1))
    _add(db, "open", today + timedelta(days=10))
    _add(db, "no-deadline", None)

    result = purge_stale_closed_announcements(db)

    assert result["deleted"] == 1
    # 기한미정(reception_end=NULL)은 마감 판단 근거가 없어 남긴다.
    assert _remaining(db) == {"recent-closed", "open", "no-deadline"}


def test_keeps_announcements_saved_by_users(db, make_user):
    """사용자가 저장한 공고는 기본값(keep_saved=True)에서 지우지 않는다.

    FK가 ON DELETE CASCADE라 지우면 마이페이지의 저장 공고까지 함께 사라진다.
    """
    user = make_user()
    old_end = date.today() - timedelta(days=RECENT_CLOSED_DAYS + 1)
    saved_id = _add(db, "old-saved", old_end)
    _add(db, "old-unsaved", old_end)
    db.add(SavedAnnouncement(id=str(uuid.uuid4()), user_id=user["userId"], announcement_id=saved_id))
    db.commit()

    result = purge_stale_closed_announcements(db)

    assert result == {
        "cutoff": (date.today() - timedelta(days=RECENT_CLOSED_DAYS)).isoformat(),
        "matched": 2,
        "deleted": 1,
        "kept_saved": 1,
    }
    assert _remaining(db) == {"old-saved"}


def test_include_saved_deletes_saved_too(db, make_user):
    user = make_user()
    old_end = date.today() - timedelta(days=RECENT_CLOSED_DAYS + 1)
    saved_id = _add(db, "old-saved", old_end)
    db.add(SavedAnnouncement(id=str(uuid.uuid4()), user_id=user["userId"], announcement_id=saved_id))
    db.commit()

    result = purge_stale_closed_announcements(db, keep_saved=False)

    assert result["deleted"] == 1
    assert _remaining(db) == set()
    # CASCADE로 저장 공고 행도 같이 지워진다.
    assert db.execute(select(SavedAnnouncement)).scalars().all() == []


def test_dry_run_reports_without_deleting(db):
    _add(db, "old", date.today() - timedelta(days=RECENT_CLOSED_DAYS + 1))

    result = purge_stale_closed_announcements(db, dry_run=True)

    assert result["deleted"] == 1
    assert _remaining(db) == {"old"}


def test_custom_days(db):
    _add(db, "closed-40d", date.today() - timedelta(days=40))

    assert purge_stale_closed_announcements(db, days=60, dry_run=True)["deleted"] == 0
    assert purge_stale_closed_announcements(db, days=20, dry_run=True)["deleted"] == 1


def test_notification_history_survives_purge(db, make_user):
    """공고가 정리돼도 알림 이력은 남고 링크(announcement_id)만 끊긴다.

    FK가 ON DELETE SET NULL이라 "내가 이 알림을 받았다"는 기록이 보관 기간 정리로
    사라지지 않는다.
    """
    user = make_user()
    ann_id = _add(db, "old-notified", date.today() - timedelta(days=RECENT_CLOSED_DAYS + 1))
    db.add(
        NotificationLog(
            id=str(uuid.uuid4()),
            user_id=user["userId"],
            announcement_id=ann_id,
            notify_type="신규매칭",
            title="공고 old-notified",
        )
    )
    db.commit()

    assert purge_stale_closed_announcements(db)["deleted"] == 1

    logs = db.execute(select(NotificationLog)).scalars().all()
    assert len(logs) == 1
    assert logs[0].announcement_id is None
    assert logs[0].title == "공고 old-notified"


def test_collect_cycle_purges_stale(db, monkeypatch):
    """수집 사이클이 끝날 때 오래된 마감 공고를 자동으로 정리한다."""
    from app.services import collect_cycle as cycle

    _add(db, "old", date.today() - timedelta(days=RECENT_CLOSED_DAYS + 1))
    _add(db, "open", date.today() + timedelta(days=10))

    async def fake_collect_all(bgn, end):
        return {"kstartup": [], "narajangteo": [], "msit": []}

    monkeypatch.setattr(cycle, "collect_all", fake_collect_all)
    monkeypatch.setattr(cycle, "generate_keyword_match_notifications", lambda db: 0)
    monkeypatch.setattr(cycle, "send_pending_notification_emails", lambda db: 0)

    summary = asyncio.run(cycle.run_collect_cycle())

    assert summary["purged"] == 1
    # 사이클은 자기 세션(SessionLocal)으로 지운다 — 이 테스트 세션이 들고 있는
    # 트랜잭션 스냅샷을 버려야 삭제 결과가 보인다.
    db.rollback()
    assert _remaining(db) == {"open"}

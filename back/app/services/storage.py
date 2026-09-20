"""collector.py가 정규화한 공고 목록을 announcements 테이블에 upsert하고,
보관 기간이 지난 공고를 정리한다."""
import uuid
from datetime import date, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from app.db.models import Announcement, SavedAnnouncement
from app.services.collector import RECENT_CLOSED_DAYS


def save_announcements(db: Session, items: list[dict]) -> int:
    """(source, external_id) UNIQUE 기준으로 upsert. 저장된(삽입+갱신) 건수를 반환.

    MySQL 전환 노트: Postgres의 on_conflict_do_update 대신
    INSERT ... ON DUPLICATE KEY UPDATE를 사용합니다. 이미 있는 (source, external_id)
    행이면 id(VALUES의 새 uuid)는 버려지고 기존 행이 갱신됩니다.
    """
    rows = [
        {
            "id": str(uuid.uuid4()),  # MySQL엔 DB측 uuid 기본값이 없어 앱에서 생성
            "source": item["source"],
            "external_id": item["external_id"],
            "title": item["title"],
            "department": item.get("department") or item.get("agency"),
            "reception_start": item.get("start_date"),
            "reception_end": item.get("end_date"),
            "status": item.get("status"),
            "detail_url": item.get("original_url"),
            "summary": item.get("content"),
        }
        for item in items
        if item.get("external_id") and item.get("title")
    ]
    if not rows:
        return 0

    stmt = insert(Announcement).values(rows)
    stmt = stmt.on_duplicate_key_update(
        title=stmt.inserted.title,
        department=stmt.inserted.department,
        reception_start=stmt.inserted.reception_start,
        reception_end=stmt.inserted.reception_end,
        status=stmt.inserted.status,
        detail_url=stmt.inserted.detail_url,
        summary=stmt.inserted.summary,
    )
    db.execute(stmt)
    db.commit()
    return len(rows)


def purge_stale_closed_announcements(
    db: Session,
    days: int = RECENT_CLOSED_DAYS,
    *,
    keep_saved: bool = True,
    dry_run: bool = False,
) -> dict:
    """마감된 지 `days`일이 지난 공고를 DB에서 지운다. 처리 건수를 돌려준다.

    수집기(collector.py)가 RECENT_CLOSED_DAYS 이내 마감 공고만 담는 것과 짝을 이루는 정리
    단계다 — 수집 필터는 "새로 안 가져오는" 것일 뿐이라, 이미 저장된 행은 이 함수가 지워야
    목록 기준이 실제로 유지된다. 매 수집 사이클 끝에 호출된다(services/collect_cycle.py).

    reception_end가 NULL인 공고(과기정통부처럼 원본에 접수기간이 없는 "기한미정")는
    마감 여부를 판단할 근거가 없어 대상에서 제외한다.

    사용자가 저장한 공고(saved_announcements)는 기본적으로 건너뛴다 — FK가 CASCADE라
    지우면 마이페이지의 저장 목록에서 말없이 사라지는데, 저장은 사용자가 직접 한 행동이라
    보관 기간 규칙으로 덮어쓸 대상이 아니다. keep_saved=False면 이것까지 지운다.

    알림 이력(notification_logs)은 막지 않는다 — FK가 ON DELETE SET NULL이라 공고가
    지워져도 알림 행은 남고 링크만 끊긴다(db/models.py).
    """
    cutoff = date.today() - timedelta(days=days)
    stale = [Announcement.reception_end.is_not(None), Announcement.reception_end < cutoff]
    saved = Announcement.id.in_(select(SavedAnnouncement.announcement_id))

    matched = db.scalar(select(func.count()).select_from(Announcement).where(*stale)) or 0
    kept = db.scalar(select(func.count()).select_from(Announcement).where(*stale, saved)) or 0

    target = [*stale, ~saved] if keep_saved else stale
    if dry_run:
        deleted = matched - kept if keep_saved else matched
    else:
        result = db.execute(delete(Announcement).where(*target))
        db.commit()
        deleted = result.rowcount

    return {
        "cutoff": cutoff.isoformat(),
        "matched": matched,
        "deleted": deleted,
        "kept_saved": kept if keep_saved else 0,
    }

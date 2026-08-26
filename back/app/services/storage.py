"""collector.py가 정규화한 공고 목록을 announcements 테이블에 upsert."""
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import Announcement


def save_announcements(db: Session, items: list[dict]) -> int:
    """(source, external_id) 기준으로 upsert. 저장된(삽입+갱신) 건수를 반환."""
    rows = [
        {
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
    stmt = stmt.on_conflict_do_update(
        index_elements=["source", "external_id"],
        set_={
            "title": stmt.excluded.title,
            "department": stmt.excluded.department,
            "reception_start": stmt.excluded.reception_start,
            "reception_end": stmt.excluded.reception_end,
            "status": stmt.excluded.status,
            "detail_url": stmt.excluded.detail_url,
            "summary": stmt.excluded.summary,
        },
    )
    db.execute(stmt)
    db.commit()
    return len(rows)

"""collector.py가 정규화한 공고 목록을 announcements 테이블에 upsert."""
import uuid

from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from app.db.models import Announcement


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

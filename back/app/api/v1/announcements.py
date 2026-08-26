"""저장된 공고 재조회 (WBS 4.6 완료 기준 확인용 — 간단 목록 조회만)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Announcement
from app.db.session import get_db

router = APIRouter(tags=["announcements"])


@router.get("/announcements")
def list_announcements(
    limit: int = Query(20, ge=1, le=100),
    source: str | None = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(Announcement).order_by(Announcement.collected_at.desc()).limit(limit)
    if source:
        stmt = stmt.where(Announcement.source == source)

    rows = db.execute(stmt).scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(r.id),
                "source": r.source,
                "external_id": r.external_id,
                "title": r.title,
                "department": r.department,
                "reception_start": r.reception_start,
                "reception_end": r.reception_end,
                "status": r.status,
                "detail_url": r.detail_url,
                "collected_at": r.collected_at,
            }
            for r in rows
        ],
    }

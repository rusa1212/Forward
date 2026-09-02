"""대시보드 집계 API (7주차 작업 순서 4)

대시보드가 그동안 mock 데이터로 보여주던 통계/매칭공고/저장공고를 실제 DB로 대체한다.
announcements.py의 직렬화/정렬/상태라벨 로직을 그대로 재사용해 중복을 만들지 않는다.
"""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.v1.announcements import SORT_OPTIONS, _serialize, _status_label_expr
from app.api.v1.auth import get_current_user
from app.db.models import Announcement, Keyword, SavedAnnouncement, User
from app.db.session import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

MATCHED_FEED_LIMIT = 10


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    keyword_names = db.execute(
        select(Keyword.keyword).where(Keyword.user_id == current_user.id)
    ).scalars().all()

    if keyword_names:
        match_condition = or_(*(Announcement.title.ilike(f"%{kw}%") for kw in keyword_names))

        matched_count = db.execute(
            select(func.count()).select_from(Announcement).where(match_condition)
        ).scalar_one()
        new_today_count = db.execute(
            select(func.count())
            .select_from(Announcement)
            .where(match_condition, func.date(Announcement.collected_at) == date.today())
        ).scalar_one()
        urgent_count = db.execute(
            select(func.count())
            .select_from(Announcement)
            .where(match_condition, _status_label_expr() == "마감임박")
        ).scalar_one()

        matched_rows = db.execute(
            select(Announcement)
            .where(match_condition)
            .order_by(*SORT_OPTIONS["latest"])
            .limit(MATCHED_FEED_LIMIT)
        ).scalars().all()
    else:
        matched_count = new_today_count = urgent_count = 0
        matched_rows = []

    saved_stmt = (
        select(Announcement)
        .join(SavedAnnouncement, SavedAnnouncement.announcement_id == Announcement.id)
        .where(SavedAnnouncement.user_id == current_user.id)
        .order_by(SavedAnnouncement.saved_at.desc())
    )
    saved_rows = db.execute(saved_stmt).scalars().all()

    return {
        "success": True,
        "data": {
            "counts": {
                "matched": matched_count,
                "newToday": new_today_count,
                "urgent": urgent_count,
                "saved": len(saved_rows),
            },
            "matched": [_serialize(row) for row in matched_rows],
            "saved": [_serialize(row) for row in saved_rows],
        },
    }

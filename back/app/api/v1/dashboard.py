"""대시보드 집계 API (5주차 파트별 작업 우선순위 BE 5번)

로그인 사용자의 등록 키워드를 기준으로 아래 4가지를 한 번에 집계해서 내려줍니다.
- matched   : 내 키워드에 매칭되는 전체 공고
- newToday  : matched 중 오늘 접수 시작한 공고
- urgent    : matched 중 마감임박(announcements.py의 statusLabel 기준) 공고
- saved     : 내가 저장한 공고 (SavedAnnouncement)

매칭 기준: 키워드가 공고 제목(title)에 부분 포함되는지로 판단합니다.
(키워드-공고 매칭을 위한 별도 테이블이 없어서, 공고 검색(announcements.py)의
`q` 필터와 동일한 방식(title ilike %keyword%)을 그대로 재사용했습니다.)

DB 전환 노트: id는 6주차 MySQL 전환으로 CHAR(36) 문자열입니다(announcements.py/keywords.py와 동일).
"""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.v1.announcements import _dday, _status_label
from app.api.v1.auth import get_current_user
from app.db.models import Announcement, Keyword, SavedAnnouncement, User
from app.db.session import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# 리스트로 내려주는 개수 제한 (개수 집계 자체는 전체 건수를 그대로 반환)
LIST_LIMIT = 20


def _matched_keywords(title: str, keywords: list[str]) -> list[str]:
    return [k for k in keywords if k in title]


def _serialize(row: Announcement, keywords: list[str]) -> dict:
    return {
        "id": str(row.id),
        "source": row.source,
        "title": row.title,
        "department": row.department,
        "reception_start": row.reception_start,
        "reception_end": row.reception_end,
        "statusLabel": _status_label(row.reception_start, row.reception_end),
        "detail_url": row.detail_url,
        "dday": _dday(row.reception_end),
        "matchedKeywords": _matched_keywords(row.title, keywords),
    }


@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    keywords = db.execute(
        select(Keyword.keyword).where(Keyword.user_id == current_user.id)
    ).scalars().all()

    if keywords:
        title_conditions = [Announcement.title.ilike(f"%{k}%") for k in keywords]
        matched_stmt = (
            select(Announcement)
            .where(or_(*title_conditions))
            .order_by(Announcement.reception_start.desc(), Announcement.id.desc())
        )
        matched_rows = db.execute(matched_stmt).scalars().all()
    else:
        matched_rows = []

    today = date.today()
    new_today_rows = [row for row in matched_rows if row.reception_start == today]
    urgent_rows = [
        row for row in matched_rows if _status_label(row.reception_start, row.reception_end) == "마감임박"
    ]

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
                "matched": len(matched_rows),
                "newToday": len(new_today_rows),
                "urgent": len(urgent_rows),
                "saved": len(saved_rows),
            },
            "matched": [_serialize(row, keywords) for row in matched_rows[:LIST_LIMIT]],
            "newToday": [_serialize(row, keywords) for row in new_today_rows[:LIST_LIMIT]],
            "urgent": [_serialize(row, keywords) for row in urgent_rows[:LIST_LIMIT]],
            "saved": [_serialize(row, keywords) for row in saved_rows[:LIST_LIMIT]],
        },
    }
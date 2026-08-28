"""저장공고(즐겨찾기) CRUD (5주차 1차 작업 순서 12)

인증된 사용자만 자신이 저장한 공고를 조회·저장·저장취소할 수 있습니다.
"""
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.errors import AppError
from app.db.models import Announcement, SavedAnnouncement, User
from app.db.session import get_db

router = APIRouter(prefix="/saved-announcements", tags=["saved-announcements"])


def _serialize(row: SavedAnnouncement, announcement: Announcement) -> dict:
    return {
        "id": str(row.id),
        "savedAt": row.saved_at,
        "announcement": {
            "id": str(announcement.id),
            "title": announcement.title,
            "department": announcement.department,
            "status": announcement.status,
            "receptionStart": announcement.reception_start,
            "receptionEnd": announcement.reception_end,
            "detailUrl": announcement.detail_url,
        },
    }


@router.get("")
def list_saved_announcements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(SavedAnnouncement, Announcement)
        .join(Announcement, Announcement.id == SavedAnnouncement.announcement_id)
        .where(SavedAnnouncement.user_id == current_user.id)
        .order_by(SavedAnnouncement.saved_at.desc())
    )
    rows = db.execute(stmt).all()
    return {"success": True, "data": [_serialize(saved, announcement) for saved, announcement in rows]}


class SaveAnnouncementRequest(BaseModel):
    announcementId: str


@router.post("")
def save_announcement(
    body: SaveAnnouncementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        parsed_announcement_id = uuid.UUID(body.announcementId)
    except ValueError:
        raise AppError(404, "ANNOUNCEMENT_NOT_FOUND", "존재하지 않는 공고입니다.")

    announcement = db.get(Announcement, parsed_announcement_id)
    if announcement is None:
        raise AppError(404, "ANNOUNCEMENT_NOT_FOUND", "존재하지 않는 공고입니다.")

    exists = db.execute(
        select(SavedAnnouncement).where(
            SavedAnnouncement.user_id == current_user.id,
            SavedAnnouncement.announcement_id == parsed_announcement_id,
        )
    ).scalar_one_or_none()
    if exists is not None:
        raise AppError(409, "ALREADY_SAVED", "이미 저장한 공고입니다.")

    row = SavedAnnouncement(user_id=current_user.id, announcement_id=parsed_announcement_id)
    db.add(row)
    db.commit()
    db.refresh(row)

    return {"success": True, "data": _serialize(row, announcement)}


@router.delete("/{announcement_id}")
def unsave_announcement(
    announcement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        parsed_announcement_id = uuid.UUID(announcement_id)
    except ValueError:
        raise AppError(404, "SAVED_ANNOUNCEMENT_NOT_FOUND", "저장한 공고를 찾을 수 없습니다.")

    row = db.execute(
        select(SavedAnnouncement).where(
            SavedAnnouncement.user_id == current_user.id,
            SavedAnnouncement.announcement_id == parsed_announcement_id,
        )
    ).scalar_one_or_none()
    if row is None:
        raise AppError(404, "SAVED_ANNOUNCEMENT_NOT_FOUND", "저장한 공고를 찾을 수 없습니다.")

    db.delete(row)
    db.commit()

    return {"success": True, "data": {"message": "저장이 취소되었습니다."}}

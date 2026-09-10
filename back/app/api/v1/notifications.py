"""알림 목록/읽음 처리 API (5주차 우선순위 P1 "알림 저장 구조").

`notification_logs` 테이블(app/db/models.py의 NotificationLog)에 쌓인 알림 이력을
조회/읽음 처리하는 API만 담당한다. 실제로 이 테이블에 알림을 "쌓는" 로직(06시 수집 →
키워드 매칭/마감임박 판정 → 알림 생성, 이메일 발송)은 별도 작업(알림·이메일 발송
자동화 파이프라인)이며 이번 범위에 포함되지 않는다.

FE `AlertsDropdown.tsx`가 필요로 하는 모양(제목, 시간, 키워드, 안읽음 여부)에 맞춰
title/keyword/createdAt/isRead를 내려준다. 실제 "n분 전" 같은 상대 시간 표기는 FE에서
createdAt을 가공해서 만든다(서버는 절대 시각만 내려줌).
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.errors import AppError
from app.db.models import Keyword, NotificationLog, User
from app.db.session import get_db

router = APIRouter(prefix="/notifications", tags=["notifications"])

LIST_LIMIT = 50


def _serialize(row: NotificationLog, keyword: Keyword | None) -> dict:
    return {
        "id": str(row.id),
        "notifyType": row.notify_type,
        "title": row.title,
        "keyword": keyword.keyword if keyword else None,
        "announcementId": str(row.announcement_id) if row.announcement_id else None,
        "isRead": row.is_read,
        "createdAt": row.created_at,
    }


@router.get("")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내 알림 목록. 최신순, 최대 LIST_LIMIT건. 안읽은 개수(unreadCount)도 함께 내려준다."""
    stmt = (
        select(NotificationLog, Keyword)
        .outerjoin(Keyword, Keyword.id == NotificationLog.keyword_id)
        .where(NotificationLog.user_id == current_user.id)
        .order_by(NotificationLog.created_at.desc())
        .limit(LIST_LIMIT)
    )
    rows = db.execute(stmt).all()

    unread_count = db.execute(
        select(NotificationLog)
        .where(NotificationLog.user_id == current_user.id, NotificationLog.is_read.is_(False))
    ).scalars().all()

    return {
        "success": True,
        "data": {
            "unreadCount": len(unread_count),
            "notifications": [_serialize(log, keyword) for log, keyword in rows],
        },
    }


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """알림 1건 읽음 처리. 남의 알림이거나 없는 id면 404 (RLS가 없으므로 user_id 조건 필수)."""
    try:
        parsed_id = str(uuid.UUID(notification_id))  # CHAR(36) PK — 문자열로 비교
    except ValueError:
        raise AppError(404, "NOTIFICATION_NOT_FOUND", "알림을 찾을 수 없습니다.")

    row = db.execute(
        select(NotificationLog).where(
            NotificationLog.id == parsed_id,
            NotificationLog.user_id == current_user.id,
        )
    ).scalar_one_or_none()
    if row is None:
        raise AppError(404, "NOTIFICATION_NOT_FOUND", "알림을 찾을 수 없습니다.")

    if not row.is_read:
        row.is_read = True
        db.commit()

    return {"success": True, "data": {"message": "읽음 처리되었습니다."}}


@router.post("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내 알림 전체 읽음 처리 (AlertsDropdown.tsx의 "모두 읽음" 버튼용)."""
    rows = db.execute(
        select(NotificationLog).where(
            NotificationLog.user_id == current_user.id,
            NotificationLog.is_read.is_(False),
        )
    ).scalars().all()

    for row in rows:
        row.is_read = True
    db.commit()

    return {"success": True, "data": {"message": "모두 읽음 처리되었습니다.", "count": len(rows)}}

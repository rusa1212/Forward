"""공고 조회 API (5주차 1차 작업 순서 8)

- GET /announcements       : 검색어·상태·기관·출처 필터 + 정렬 + 페이지네이션
- GET /announcements/{id}  : 공고 상세 (없으면 404)

상태값 정규화:
수집 출처(app/services/collector.py)마다 원본 상태값이 다릅니다
(K-Startup은 "Y"/"N", 나라장터는 공고 종류명, 과기정통부는 없음(null)).
그래서 원본 `status` 컬럼과는 별도로, 접수시작일/접수종료일을 기준으로
FE의 StatusType(접수중/접수예정/마감임박/마감)에 맞춘 `statusLabel`을 계산해서 내려줍니다.
- 마감임박 기준은 "마감일까지 3일 이내"로 잡았습니다(팀 협의된 값이 아니라 임시 기준이니,
  FE 연동 시 실제 기준을 다시 확인해주세요).
- 접수시작일/종료일 정보가 아예 없는 공고(예: msit)는 판단할 수 없어 statusLabel이 null입니다.
"""
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, literal, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import Announcement
from app.db.session import get_db

router = APIRouter(tags=["announcements"])

# 5-1plan.md "정렬 권장 기준" 표 그대로 반영
SORT_OPTIONS = {
    "latest": (Announcement.reception_start.desc(), Announcement.id.desc()),
    "deadline": (Announcement.reception_end.asc().nulls_last(), Announcement.id.asc()),
    "title": (Announcement.title.asc(), Announcement.id.asc()),
}

DEADLINE_SOON_DAYS = 3
STATUS_LABELS = ("접수중", "접수예정", "마감임박", "마감")


def _status_label_expr():
    """statusLabel을 SQL에서 계산 (WHERE 필터가 페이지네이션과 같이 정확히 동작하도록)."""
    today = func.current_date()
    return case(
        (Announcement.reception_start.is_(None) & Announcement.reception_end.is_(None), literal(None)),
        (Announcement.reception_end < today, "마감"),
        (Announcement.reception_start > today, "접수예정"),
        (Announcement.reception_end <= today + timedelta(days=DEADLINE_SOON_DAYS), "마감임박"),
        else_="접수중",
    )


def _status_label(reception_start: date | None, reception_end: date | None) -> str | None:
    """statusLabel을 파이썬에서 계산 (_status_label_expr()과 동일한 규칙, 응답 직렬화용)."""
    if reception_start is None and reception_end is None:
        return None
    today = date.today()
    if reception_end is not None and reception_end < today:
        return "마감"
    if reception_start is not None and reception_start > today:
        return "접수예정"
    if reception_end is not None and reception_end <= today + timedelta(days=DEADLINE_SOON_DAYS):
        return "마감임박"
    return "접수중"


def _dday(reception_end: date | None) -> int | None:
    """오늘 기준 마감일까지 남은 일수. 마감일 정보가 없으면 null."""
    if reception_end is None:
        return None
    return (reception_end - date.today()).days


def _serialize(row: Announcement) -> dict:
    return {
        "id": str(row.id),
        "source": row.source,
        "external_id": row.external_id,
        "title": row.title,
        "department": row.department,
        "reception_start": row.reception_start,
        "reception_end": row.reception_end,
        "status": row.status,
        "statusLabel": _status_label(row.reception_start, row.reception_end),
        "detail_url": row.detail_url,
        "summary": row.summary,
        "collected_at": row.collected_at,
        "dday": _dday(row.reception_end),
    }


@router.get("/announcements")
def list_announcements(
    q: str | None = Query(None, description="제목 검색어 (부분 일치)"),
    status: str | None = Query(None, description="공고 상태 필터 (저장된 원본 값과 정확히 일치해야 함)"),
    statusLabel: str | None = Query(
        None, description=f"정규화된 상태 필터: {', '.join(STATUS_LABELS)} 중 하나"
    ),
    department: str | None = Query(None, description="기관/부서 필터"),
    source: str | None = Query(None, description="수집 출처 필터 (kstartup, narajangteo, msit)"),
    sort: str = Query("latest", description="정렬 기준: latest | deadline | title"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 개수"),
    db: Session = Depends(get_db),
):
    if sort not in SORT_OPTIONS:
        raise AppError(400, "INVALID_SORT", "sort는 latest, deadline, title 중 하나여야 합니다.")
    if statusLabel is not None and statusLabel not in STATUS_LABELS:
        raise AppError(
            400, "INVALID_STATUS_LABEL", f"statusLabel은 {', '.join(STATUS_LABELS)} 중 하나여야 합니다."
        )

    conditions = []
    if q:
        conditions.append(Announcement.title.ilike(f"%{q}%"))
    if status:
        conditions.append(Announcement.status == status)
    if statusLabel:
        conditions.append(_status_label_expr() == statusLabel)
    if department:
        conditions.append(Announcement.department == department)
    if source:
        conditions.append(Announcement.source == source)

    count_stmt = select(func.count()).select_from(Announcement)
    list_stmt = select(Announcement)
    for condition in conditions:
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)

    total = db.execute(count_stmt).scalar_one()

    list_stmt = (
        list_stmt.order_by(*SORT_OPTIONS[sort]).offset((page - 1) * page_size).limit(page_size)
    )
    rows = db.execute(list_stmt).scalars().all()

    return {
        "success": True,
        "data": [_serialize(row) for row in rows],
        "meta": {"total": total, "page": page, "page_size": page_size},
    }


@router.get("/announcements/{announcement_id}")
def get_announcement(announcement_id: str, db: Session = Depends(get_db)):
    try:
        parsed_id = uuid.UUID(announcement_id)
    except ValueError:
        raise AppError(404, "ANNOUNCEMENT_NOT_FOUND", "존재하지 않는 공고입니다.")

    row = db.get(Announcement, parsed_id)
    if row is None:
        raise AppError(404, "ANNOUNCEMENT_NOT_FOUND", "존재하지 않는 공고입니다.")

    return {"success": True, "data": _serialize(row)}

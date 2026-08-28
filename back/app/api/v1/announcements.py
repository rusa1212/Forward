"""공고 조회 API (5주차 1차 작업 순서 8)

- GET /announcements       : 검색어·상태·기관·출처 필터 + 정렬 + 페이지네이션
- GET /announcements/{id}  : 공고 상세 (없으면 404)

주의: `status`는 아직 원본 데이터(source마다 다른 문자열, 예: "Y"/"N", "일반공고" 등)를
그대로 저장하고 있어서(app/services/collector.py 참고), FE의 접수중/마감 같은 정규화된
값과는 다를 수 있습니다. 상태값을 통일하는 작업은 이번 범위에 포함하지 않았고,
지금은 저장된 값 그대로 필터링만 됩니다 (FE 연동 시 다시 논의 필요).
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
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
        "detail_url": row.detail_url,
        "summary": row.summary,
        "collected_at": row.collected_at,
        "dday": _dday(row.reception_end),
    }


@router.get("/announcements")
def list_announcements(
    q: str | None = Query(None, description="제목 검색어 (부분 일치)"),
    status: str | None = Query(None, description="공고 상태 필터 (저장된 값과 정확히 일치해야 함)"),
    department: str | None = Query(None, description="기관/부서 필터"),
    source: str | None = Query(None, description="수집 출처 필터 (kstartup, narajangteo, msit)"),
    sort: str = Query("latest", description="정렬 기준: latest | deadline | title"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 개수"),
    db: Session = Depends(get_db),
):
    if sort not in SORT_OPTIONS:
        raise AppError(400, "INVALID_SORT", "sort는 latest, deadline, title 중 하나여야 합니다.")

    conditions = []
    if q:
        conditions.append(Announcement.title.ilike(f"%{q}%"))
    if status:
        conditions.append(Announcement.status == status)
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

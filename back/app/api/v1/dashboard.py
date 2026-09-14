"""대시보드 집계 API (7주차 작업 순서 4)

대시보드가 그동안 mock 데이터로 보여주던 통계/매칭공고/저장공고를 실제 DB로 대체한다.
announcements.py의 직렬화/정렬/상태라벨 로직을 그대로 재사용해 중복을 만들지 않는다.
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.v1.announcements import SORT_OPTIONS, _collected_today_expr, _serialize, _status_label_expr, _today_kst
from app.api.v1.auth import get_current_user
from app.db.models import Announcement, Keyword, SavedAnnouncement, User
from app.db.session import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

MATCHED_FEED_LIMIT = 10
MONTH_LABELS = [f"{m}월" for m in range(1, 13)]


def _user_keywords(db: Session, current_user: User) -> list[str]:
    return db.execute(
        select(Keyword.keyword).where(Keyword.user_id == current_user.id)
    ).scalars().all()


def _match_condition(keyword_names: list[str]):
    """키워드 제목 부분일치(ILIKE)의 OR 조건. 키워드가 없으면 None."""
    if not keyword_names:
        return None
    return or_(*(Announcement.title.ilike(f"%{kw}%") for kw in keyword_names))


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    keyword_names = _user_keywords(db, current_user)
    match_condition = _match_condition(keyword_names)

    if match_condition is not None:
        matched_count = db.execute(
            select(func.count()).select_from(Announcement).where(match_condition)
        ).scalar_one()
        new_today_count = db.execute(
            select(func.count())
            .select_from(Announcement)
            .where(match_condition, _collected_today_expr())
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

        # "마감 임박" 위젯(UrgentPanel.tsx) 전용 목록. matched_rows(최신순 상위
        # MATCHED_FEED_LIMIT건)에서 다시 걸러내면, 정작 마감임박인 공고가 최신 10건
        # 밖에 있을 때 urgent_count(집계)와 위젯에 뜨는 실제 목록이 서로 달라진다
        # (R&D Monitor 회의 피드백 5번) — 그래서 별도로 마감 임박 기준(_status_label_expr)에
        # 맞춰 마감일 오름차순으로 직접 조회한다.
        urgent_rows = db.execute(
            select(Announcement)
            .where(match_condition, _status_label_expr() == "마감임박")
            .order_by(Announcement.reception_end.asc())
            .limit(MATCHED_FEED_LIMIT)
        ).scalars().all()
    else:
        matched_count = new_today_count = urgent_count = 0
        matched_rows = []
        urgent_rows = []

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
            "urgent": [_serialize(row) for row in urgent_rows],
            "saved": [_serialize(row) for row in saved_rows],
        },
    }


@router.get("/trend")
def get_dashboard_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """월별 키워드 매칭 추이 — 올해·작년의 1~12월 매칭 건수(각 12개 배열).

    매칭 기준은 /dashboard/summary와 동일(키워드 제목 부분일치의 OR), 집계 기준은
    공고가 "몇 월에 수집됐는지"(collected_at). collected_at은 UTC로 저장되므로
    KST로 변환한 뒤 연/월을 뽑는다(_today_kst()와 같은 이유 — 위 주석 참고).
    """
    keyword_names = _user_keywords(db, current_user)
    match_condition = _match_condition(keyword_names)

    curr_year = _today_kst().year
    prev_year = curr_year - 1
    counts = {prev_year: [0] * 12, curr_year: [0] * 12}

    if match_condition is not None:
        collected_kst = func.convert_tz(Announcement.collected_at, "+00:00", "+09:00")
        year_expr = func.year(collected_kst)
        month_expr = func.month(collected_kst)

        rows = db.execute(
            select(year_expr, month_expr, func.count())
            .where(
                match_condition,
                collected_kst >= datetime(prev_year, 1, 1),
                collected_kst < datetime(curr_year + 1, 1, 1),
            )
            .group_by(year_expr, month_expr)
        ).all()

        for year, month, count in rows:
            counts[int(year)][int(month) - 1] = count

    return {
        "success": True,
        "data": {
            "months": MONTH_LABELS,
            "series": [
                {"year": prev_year, "counts": counts[prev_year]},
                {"year": curr_year, "counts": counts[curr_year]},
            ],
        },
    }

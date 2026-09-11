"""대시보드 집계 API (7주차 작업 순서 4)

대시보드가 그동안 mock 데이터로 보여주던 통계/매칭공고/저장공고를 실제 DB로 대체한다.
announcements.py의 직렬화/정렬/상태라벨 로직을 그대로 재사용해 중복을 만들지 않는다.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.v1.announcements import SORT_OPTIONS, _serialize, _status_label_expr
from app.api.v1.auth import get_current_user
from app.db.models import Announcement, Keyword, SavedAnnouncement, User
from app.db.session import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

MATCHED_FEED_LIMIT = 10
MONTH_LABELS = [f"{m}월" for m in range(1, 13)]

# collected_at은 항상 UTC로 저장된다(session.py). "오늘"은 사용자 기준(KST)이라서
# UTC 그대로 date.today()나 utcnow().date()와 비교하면 하루 중 특정 시간대(특히 매일
# 06:00 KST 자동 수집 직후)에 newToday가 실제로는 오늘 수집된 공고인데도 0으로 나온다.
# collected_at을 KST로 변환한 뒤 KST 기준 "오늘"과 비교해야 서버 OS 타임존과 무관하게 맞는다.
KST_OFFSET = timedelta(hours=9)


def _today_kst():
    return (datetime.utcnow() + KST_OFFSET).date()


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
            .where(
                match_condition,
                func.date(func.convert_tz(Announcement.collected_at, "+00:00", "+09:00")) == _today_kst(),
            )
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

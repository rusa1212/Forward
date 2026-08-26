"""공고 수집 트리거. GET은 미리보기(저장 안 함), POST는 실제로 DB에 저장."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.collector import collect_all
from app.services.storage import save_announcements

router = APIRouter(tags=["collect"])


def _bid_date_range(bid_from: str | None, bid_to: str | None) -> tuple[str, str]:
    today = datetime.now().strftime("%Y%m%d")
    return bid_from or f"{today}0000", bid_to or f"{today}2359"


@router.get("/collect")
async def collect(
    bid_from: str | None = Query(None, description="나라장터 조회 시작 YYYYMMDDHHMM (기본: 오늘 00:00)"),
    bid_to: str | None = Query(None, description="나라장터 조회 종료 YYYYMMDDHHMM (기본: 오늘 23:59)"),
):
    """미리보기용. DB에 저장하지 않고 수집 결과만 반환."""
    inqry_bgn_dt, inqry_end_dt = _bid_date_range(bid_from, bid_to)
    result = await collect_all(inqry_bgn_dt, inqry_end_dt)
    return {
        "success": True,
        "data": {
            "counts": {source: len(items) for source, items in result.items()},
            "items": result,
        },
    }


@router.post("/collect")
async def collect_and_save(
    bid_from: str | None = Query(None, description="나라장터 조회 시작 YYYYMMDDHHMM (기본: 오늘 00:00)"),
    bid_to: str | None = Query(None, description="나라장터 조회 종료 YYYYMMDDHHMM (기본: 오늘 23:59)"),
    db: Session = Depends(get_db),
):
    """3개 소스를 수집해서 announcements 테이블에 upsert."""
    inqry_bgn_dt, inqry_end_dt = _bid_date_range(bid_from, bid_to)
    result = await collect_all(inqry_bgn_dt, inqry_end_dt)
    all_items = [item for items in result.values() for item in items]
    saved = save_announcements(db, all_items)

    return {
        "success": True,
        "data": {
            "fetched": {source: len(items) for source, items in result.items()},
            "saved": saved,
        },
    }

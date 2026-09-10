"""공고 수집 트리거. GET은 미리보기(저장 안 함), POST는 실제로 DB에 저장.

관리자 보호 (5주차 우선순위 P0 "POST /collect 보호"):
공공데이터포털 API를 실제로 호출하고(GET도 포함 — 호출 자체가 외부 API 쿼터를 씀) POST는
DB에 직접 쓰기까지 하므로, 아무나 호출할 수 있으면 안 된다. 매일 자동 수집은
core/scheduler.py가 이 HTTP 엔드포인트를 거치지 않고 서비스 함수를 직접 호출하므로,
여기에 관리자 인증을 걸어도 자동 수집(스케줄러)에는 영향이 없다.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_admin
from app.db.models import User
from app.db.session import get_db
from app.services.collector import collect_all, today_bid_date_range
from app.services.storage import save_announcements

router = APIRouter(tags=["collect"])


def _bid_date_range(bid_from: str | None, bid_to: str | None) -> tuple[str, str]:
    default_from, default_to = today_bid_date_range()
    return bid_from or default_from, bid_to or default_to


@router.get("/collect")
async def collect(
    bid_from: str | None = Query(None, description="나라장터 조회 시작 YYYYMMDDHHMM (기본: 오늘 00:00)"),
    bid_to: str | None = Query(None, description="나라장터 조회 종료 YYYYMMDDHHMM (기본: 오늘 23:59)"),
    _admin: User = Depends(get_current_admin),
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
    _admin: User = Depends(get_current_admin),
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

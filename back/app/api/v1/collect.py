"""공고 수집 트리거. GET은 미리보기(저장 안 함), POST는 실제로 DB에 저장.

관리자 보호 (5주차 우선순위 P0 "POST /collect 보호"):
공공데이터포털 API를 실제로 호출하고(GET도 포함 — 호출 자체가 외부 API 쿼터를 씀) POST는
DB에 직접 쓰기까지 하므로, 아무나 호출할 수 있으면 안 된다. 매일 자동 수집은
core/scheduler.py가 이 HTTP 엔드포인트를 거치지 않고 서비스 함수를 직접 호출하므로,
여기에 관리자 인증을 걸어도 자동 수집(스케줄러)에는 영향이 없다.

POST /collect/cron 은 별개다 — 서버가 잠드는 환경(Render 무료 플랜)에서 스케줄러를 대신해
외부 cron이 때리는 용도라, 만료되는 관리자 JWT 대신 고정 토큰(CRON_TOKEN)으로 인증한다.
"""
import logging
import secrets

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Query
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_admin
from app.core.config import settings
from app.core.errors import AppError
from app.db.models import User
from app.db.session import get_db
from app.services.collect_cycle import is_collect_running, run_collect_cycle
from app.services.collector import collect_all, today_bid_date_range
from app.services.storage import save_announcements

logger = logging.getLogger("app.collect")

router = APIRouter(tags=["collect"])


def _bid_date_range(bid_from: str | None, bid_to: str | None) -> tuple[str, str]:
    default_from, default_to = today_bid_date_range()
    return bid_from or default_from, bid_to or default_to


@router.get("/collect")
async def collect(
    bid_from: str | None = Query(None, description="나라장터 조회 시작 YYYYMMDDHHMM (기본: 최근 30일 전 00:00)"),
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
    bid_from: str | None = Query(None, description="나라장터 조회 시작 YYYYMMDDHHMM (기본: 최근 30일 전 00:00)"),
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


@router.post("/collect/cron", status_code=202)
async def collect_by_cron(
    background: BackgroundTasks,
    x_cron_token: str | None = Header(None, alias="X-Cron-Token"),
):
    """외부 cron 전용 수집 트리거. 스케줄러와 똑같이 수집→매칭→알림→메일까지 실행한다.

    관리자용 POST /collect와 따로 두는 이유:
      - 관리자 JWT는 24시간이면 만료돼서 cron 설정에 넣어둘 수 없다.
      - 관리자용은 DB 저장까지만 하고 알림 생성·메일 발송을 하지 않아 스케줄러와 동작이 다르다.

    바로 202를 돌려주고 실제 수집은 백그라운드로 넘긴다. 수집은 외부 API를 여러 번 호출해
    수십 초가 걸리는데, 무료 cron 서비스는 보통 30초쯤에 연결을 끊어버려서 동기로 처리하면
    매번 실패로 기록되기 때문이다. 수집 결과는 응답이 아니라 서버 로그에 남는다.
    """
    # 토큰 미설정 = 기능 자체를 안 켠 상태. 존재를 알리지 않도록 404로 응답한다.
    if not settings.CRON_TOKEN:
        raise AppError(404, "NOT_FOUND", "Not Found")

    # compare_digest: 앞에서부터 한 글자씩 비교하다 틀리면 바로 끝내는 일반 비교(==)와 달리
    # 항상 같은 시간이 걸린다. 응답 시간 차이로 토큰을 한 글자씩 알아내는 걸 막는다.
    if not x_cron_token or not secrets.compare_digest(x_cron_token, settings.CRON_TOKEN):
        raise AppError(401, "INVALID_CRON_TOKEN", "유효하지 않은 토큰입니다.")

    # 앞선 실행이 아직 도는 중이면 겹쳐 돌리지 않는다 (같은 일을 두 번 하게 된다).
    if is_collect_running():
        logger.info("cron collect skipped: 이전 수집이 아직 실행 중")
        return {"success": True, "data": {"status": "already_running"}}

    background.add_task(run_collect_cycle)
    logger.info("cron collect accepted")
    return {"success": True, "data": {"status": "accepted"}}

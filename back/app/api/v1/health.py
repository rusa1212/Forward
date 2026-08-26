"""
헬스체크 라우터 (WBS 1.1 완료 기준: "FE/BE 로컬 실행 및 상호 호출 가능" 확인용)
FE는 개발 중 이 엔드포인트로 "서버가 살아있는지 + DB가 연결되는지"를 확인할 수 있습니다.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"success": True, "data": {"status": "ok"}}


@router.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    """DB 연결까지 확인. DB 팀원의 .env가 아직 없으면 여기서 500이 나는 게 정상입니다."""
    db.execute(text("SELECT 1"))
    return {"success": True, "data": {"db": "connected"}}

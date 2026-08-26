"""헬스체크 라우터 — 서버/DB가 살아있는지 확인용"""
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
    db.execute(text("SELECT 1"))
    return {"success": True, "data": {"db": "connected"}}

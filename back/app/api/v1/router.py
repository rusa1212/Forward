"""
API v1 라우터 모음 (WBS 1.1 — 라우터 구조)

앞으로 만들 기능별 라우터는 여기 등록만 하면 됩니다.
예: 5.1/5.2 인증 -> auth.py, 3.1/3.2 공고 -> announcements.py, 7.1 키워드 -> keywords.py ...
지금은 뼈대만 있는 상태라 health만 등록되어 있습니다.
"""
from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)

# 다음에 만들 라우터들은 여기 추가:
# from app.api.v1 import auth, announcements, keywords, saved, alerts, dashboard, me
# api_router.include_router(auth.router)
# api_router.include_router(announcements.router)
# ...

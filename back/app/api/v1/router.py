from fastapi import APIRouter

from app.api.v1 import admin, announcements, auth, collect, dashboard, health, keywords
from app.api.v1 import saved_announcements
from app.api.v1 import me

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(collect.router)
api_router.include_router(announcements.router)
api_router.include_router(auth.router)
api_router.include_router(keywords.router)
api_router.include_router(saved_announcements.router)
api_router.include_router(admin.router)
api_router.include_router(dashboard.router)
api_router.include_router(me.router)

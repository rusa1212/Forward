from fastapi import APIRouter

from app.api.v1 import announcements, auth, collect, health
from app.api.v1 import saved_announcements

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(collect.router)
api_router.include_router(announcements.router)
api_router.include_router(auth.router)
api_router.include_router(saved_announcements.router)

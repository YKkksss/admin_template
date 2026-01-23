"""API 总路由入口。"""

from fastapi import APIRouter

from app.api.v1.router import router as v1_router
from app.core.config import settings

api_router = APIRouter()

# 统一挂载 v1 API
api_router.include_router(v1_router, prefix=settings.API_V1_STR)

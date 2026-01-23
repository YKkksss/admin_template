from fastapi import APIRouter

from app.schemas.response import ApiResponse, ok

router = APIRouter()


@router.get("/health", response_model=ApiResponse[dict])
async def health_check():
    """健康检查，用于联调与部署探活。"""

    return ok({"status": "ok"})

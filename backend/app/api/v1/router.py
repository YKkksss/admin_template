"""API v1 路由汇总。"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, menu, monitor, notice, system, user, ws_notice

router = APIRouter()

router.include_router(health.router, tags=["健康检查"])
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(user.router, prefix="/user", tags=["用户"])
router.include_router(menu.router, prefix="/menu", tags=["菜单"])
router.include_router(notice.router, prefix="/notice", tags=["消息通知"])
router.include_router(system.router, prefix="/system", tags=["系统"])
router.include_router(monitor.router, prefix="/monitor", tags=["监控"])
router.include_router(ws_notice.router, tags=["WebSocket"])

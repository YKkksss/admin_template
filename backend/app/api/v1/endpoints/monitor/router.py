"""监控与审计相关路由汇总。"""

from fastapi import APIRouter

from app.api.v1.endpoints.monitor import login_log, operation_log

router = APIRouter()

router.include_router(operation_log.router, prefix="/operation-log", tags=["监控-操作日志"])
router.include_router(login_log.router, prefix="/login-log", tags=["监控-登录日志"])


"""系统管理路由汇总。"""

from fastapi import APIRouter

from app.api.v1.endpoints.system import config, dept, dict, menu, notice, role, user

router = APIRouter()

router.include_router(dept.router, prefix="/dept", tags=["系统-部门"])
router.include_router(dict.router, prefix="/dict", tags=["系统-字典"])
router.include_router(config.router, prefix="/config", tags=["系统-配置"])
router.include_router(menu.router, prefix="/menu", tags=["系统-菜单"])
router.include_router(role.router, prefix="/role", tags=["系统-角色"])
router.include_router(user.router, prefix="/user", tags=["系统-用户"])
router.include_router(notice.router, prefix="/notice", tags=["系统-消息通知"])

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user
from app.schemas.response import ApiResponse, ok
from app.schemas.user import CurrentUser
from app.services.auth import auth_service

router = APIRouter()


@router.get("/all", response_model=ApiResponse[list[dict]])
async def get_all_menus(current_user: CurrentUser = Depends(get_current_user)):
    """
    获取用户菜单（用于动态路由与侧边栏渲染）。

    当前为基础占位实现，返回结构遵循前端 `@vben/access` 菜单生成器的约定字段。
    """

    return ok(await auth_service.get_menus(current_user.username))

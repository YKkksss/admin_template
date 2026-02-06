"""依赖注入（Dependencies）。"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings
from app.schemas.user import CurrentUser
from app.services.auth import auth_service
from app.services.session import session_service


async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    """
    从请求头 `Authorization: Bearer <token>` 中解析当前用户。

    说明：
    - 当前阶段仅提供基础能力，用于后续 RBAC、动态路由、按钮权限扩展。
    """

    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录信息无效")

    user = auth_service.parse_access_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录信息已过期或无效")

    ok_, reason = await session_service.validate_session(username=user.username, jti=user.jti)
    if not ok_:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=reason)

    return user


def require_superuser(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    仅允许超级管理员访问的依赖。

    说明：
    - 当前阶段以 JWT 中的 roles（角色编码）为准；
    - 超级管理员角色编码由环境变量 SUPERUSER_ROLE_CODE 控制，默认 `super`。
    """

    if settings.SUPERUSER_ROLE_CODE in current_user.roles:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")


def require_permissions(*permission_codes: str) -> Callable[[CurrentUser], CurrentUser]:
    """
    权限码校验依赖（RBAC）。

    说明：
    - 超级管理员角色（SUPERUSER_ROLE_CODE）默认放行；
    - 其他角色：根据 sys_menu.auth_code + sys_role_menu 计算可用权限码集合；
    - 当缺少任一必需权限码时，返回 403。
    """

    required = [code for code in permission_codes if code]

    async def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if settings.SUPERUSER_ROLE_CODE in current_user.roles:
            return current_user

        if not required:
            return current_user

        codes = await auth_service.get_access_codes(current_user.roles)
        if not set(required).issubset(set(codes)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

        return current_user

    return dependency

"""
认证与授权相关服务（当前为基础版本）。

说明：
1. 当前阶段：登录与用户信息从数据库读取（Tortoise ORM）。
2. 菜单与权限码：先用内置映射满足前端联调，后续再迁移到数据库与 RBAC 规则。
"""

from __future__ import annotations

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.models.role import Role
from app.models.user import User
from app.schemas.user import CurrentUser, UserInfo
from app.services.menu import get_access_codes_for_roles, get_routes_for_user


class AuthService:
    async def login(self, username: str, password: str) -> str | None:
        user = await User.get_or_none(username=username, is_active=True)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None

        roles = await user.roles.filter(status=1).all()
        role_codes = [role.code for role in roles]
        return create_access_token(subject=user.username, roles=role_codes)

    async def register(self, username: str, password: str) -> User | None:
        """
        注册新用户（基础版本）。

        说明：
        - 当前阶段默认分配 `user` 角色。
        - 仅创建账号与角色关系，后续可扩展：邮箱/手机、验证码、邀请注册等。
        """

        role, _ = await Role.get_or_create(code="user", defaults={"name": "普通用户"})

        user, created = await User.get_or_create(
            username=username,
            defaults={
                "password_hash": get_password_hash(password),
                "real_name": username,
                "is_active": True,
            },
        )
        if not created:
            return None

        await user.roles.add(role)
        return user

    def refresh_access_token(self) -> str | None:
        # 当前阶段暂不做 refreshToken 校验，直接生成一个演示 token。
        # 后续可替换为：从 HttpOnly Cookie 中读取 refreshToken -> 校验 -> 颁发新 accessToken。
        return create_access_token(subject="admin", roles=["admin"])

    def parse_access_token(self, token: str) -> CurrentUser | None:
        payload = decode_access_token(token)
        if not payload:
            return None
        username = payload.get("sub")
        roles = payload.get("roles") or []
        if not isinstance(username, str):
            return None
        if not isinstance(roles, list):
            roles = []
        roles = [str(r) for r in roles]
        return CurrentUser(username=username, roles=roles)

    async def get_user_info(self, username: str) -> UserInfo | None:
        user = await User.get_or_none(username=username, is_active=True)
        if not user:
            return None
        roles = await user.roles.filter(status=1).all()
        role_codes = [role.code for role in roles]
        return UserInfo(
            id=user.id,
            username=user.username,
            realName=user.real_name,
            roles=role_codes,
            homePath=user.home_path,
            avatar=user.avatar,
            introduction=user.introduction,
        )

    async def get_access_codes(self, roles: list[str]) -> list[str]:
        """获取权限码（由 sys_menu.auth_code 驱动）。"""

        return await get_access_codes_for_roles(roles)

    async def get_menus(self, username: str) -> list[dict]:
        """获取用户菜单（用于动态路由与侧边栏渲染）。"""

        return await get_routes_for_user(username)


auth_service = AuthService()

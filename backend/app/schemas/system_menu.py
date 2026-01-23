"""系统菜单相关 Schema（用于菜单管理与角色授权）。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SystemMenuBase(BaseModel):
    name: str = Field(..., description="菜单名称（路由 name）")
    type: str = Field(
        default="menu",
        description="菜单类型：catalog/menu/embedded/link/button",
    )
    pid: int | None = Field(default=None, description="父级菜单ID")
    path: str | None = Field(default=None, description="路由路径（按钮可为空）")
    component: str | None = Field(
        default=None,
        description="前端组件标识（如 /system/menu/list 或 IFrameView）",
    )
    activePath: str | None = Field(default=None, description="激活菜单路径（用于高亮）")
    authCode: str | None = Field(default=None, description="权限标识（菜单/按钮/接口权限码）")
    status: int = Field(default=1, description="状态：1启用 0禁用")
    meta: dict[str, Any] | None = Field(
        default_factory=dict,
        description="菜单元信息（图标、标题、排序等）",
    )


class SystemMenuCreate(SystemMenuBase):
    pass


class SystemMenuUpdate(BaseModel):
    name: str | None = Field(default=None, description="菜单名称（路由 name）")
    type: str | None = Field(
        default=None,
        description="菜单类型：catalog/menu/embedded/link/button",
    )
    pid: int | None = Field(default=None, description="父级菜单ID")
    path: str | None = Field(default=None, description="路由路径（按钮可为空）")
    component: str | None = Field(
        default=None,
        description="前端组件标识（如 /system/menu/list 或 IFrameView）",
    )
    activePath: str | None = Field(default=None, description="激活菜单路径（用于高亮）")
    authCode: str | None = Field(default=None, description="权限标识（菜单/按钮/接口权限码）")
    status: int | None = Field(default=None, description="状态：1启用 0禁用")
    meta: dict[str, Any] | None = Field(
        default=None,
        description="菜单元信息（图标、标题、排序等）",
    )


class SystemMenuOut(SystemMenuBase):
    id: int = Field(..., description="菜单ID")
    children: list[SystemMenuOut] | None = Field(default=None, description="子级菜单")


SystemMenuOut.model_rebuild()

"""系统角色相关 Schema（用于角色管理与授权）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SystemRoleBase(BaseModel):
    name: str = Field(..., description="角色名称")
    status: int = Field(default=1, description="状态：1启用 0禁用")
    remark: str | None = Field(default=None, description="备注")
    permissions: list[int] = Field(default_factory=list, description="菜单/按钮权限ID集合")


class SystemRoleCreate(SystemRoleBase):
    pass


class SystemRoleUpdate(BaseModel):
    name: str | None = Field(default=None, description="角色名称")
    status: int | None = Field(default=None, description="状态：1启用 0禁用")
    remark: str | None = Field(default=None, description="备注")
    permissions: list[int] | None = Field(default=None, description="菜单/按钮权限ID集合")


class SystemRoleOut(SystemRoleBase):
    id: int = Field(..., description="角色ID")
    createTime: str | None = Field(default=None, description="创建时间（字符串）")


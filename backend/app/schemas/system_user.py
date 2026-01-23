"""系统用户相关 Schema（用于用户管理）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SystemUserBase(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    realName: str = Field(..., min_length=1, max_length=50, description="真实姓名")
    status: int = Field(default=1, description="状态：1启用 0禁用")
    deptId: int | None = Field(default=None, description="部门ID")
    roleIds: list[int] = Field(default_factory=list, description="角色ID列表")
    avatar: str | None = Field(default=None, description="头像")
    homePath: str | None = Field(default=None, description="首页路径")


class SystemUserCreate(SystemUserBase):
    password: str = Field(..., min_length=6, description="密码（最少 6 位）")


class SystemUserUpdate(BaseModel):
    realName: str | None = Field(default=None, min_length=1, max_length=50, description="真实姓名")
    status: int | None = Field(default=None, description="状态：1启用 0禁用")
    deptId: int | None = Field(default=None, description="部门ID")
    roleIds: list[int] | None = Field(default=None, description="角色ID列表")
    avatar: str | None = Field(default=None, description="头像")
    homePath: str | None = Field(default=None, description="首页路径")


class SystemUserResetPassword(BaseModel):
    password: str = Field(..., min_length=6, description="新密码（最少 6 位）")


class SystemUserOut(BaseModel):
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    realName: str = Field(..., description="真实姓名")
    status: int = Field(..., description="状态：1启用 0禁用")
    deptId: int | None = Field(default=None, description="部门ID")
    deptName: str | None = Field(default=None, description="部门名称")
    roleIds: list[int] = Field(default_factory=list, description="角色ID列表")
    roleNames: list[str] = Field(default_factory=list, description="角色名称列表")
    avatar: str | None = Field(default=None, description="头像")
    homePath: str | None = Field(default=None, description="首页路径")
    createTime: str | None = Field(default=None, description="创建时间（字符串）")


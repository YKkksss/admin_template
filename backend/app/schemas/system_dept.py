"""系统部门相关 Schema（用于部门管理）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SystemDeptBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=20, description="部门名称")
    pid: int | None = Field(default=None, description="上级部门ID（根部门为空）")
    status: int = Field(default=1, description="状态：1启用 0禁用")
    remark: str | None = Field(default=None, max_length=50, description="备注")


class SystemDeptCreate(SystemDeptBase):
    pass


class SystemDeptUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=20, description="部门名称")
    pid: int | None = Field(default=None, description="上级部门ID（根部门为空）")
    status: int | None = Field(default=None, description="状态：1启用 0禁用")
    remark: str | None = Field(default=None, max_length=50, description="备注")


class SystemDeptOut(SystemDeptBase):
    id: int = Field(..., description="部门ID")
    createTime: str | None = Field(default=None, description="创建时间（字符串）")
    children: list["SystemDeptOut"] | None = Field(default=None, description="下级部门")


SystemDeptOut.model_rebuild()


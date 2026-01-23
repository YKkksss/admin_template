"""系统参数配置 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SystemConfigBase(BaseModel):
    configName: str = Field(..., description="配置名称")
    configKey: str = Field(..., description="配置键（唯一标识）")
    configValue: str = Field(..., description="配置值")
    status: int = Field(default=1, description="状态：1启用 0禁用")
    remark: str | None = Field(default=None, description="备注")
    isBuiltin: bool = Field(default=False, description="是否内置配置（内置配置不允许删除）")


class SystemConfigCreate(SystemConfigBase):
    pass


class SystemConfigUpdate(BaseModel):
    configName: str | None = Field(default=None, description="配置名称")
    configKey: str | None = Field(default=None, description="配置键（唯一标识）")
    configValue: str | None = Field(default=None, description="配置值")
    status: int | None = Field(default=None, description="状态：1启用 0禁用")
    remark: str | None = Field(default=None, description="备注")
    isBuiltin: bool | None = Field(default=None, description="是否内置配置（内置配置不允许删除）")


class SystemConfigOut(SystemConfigBase):
    id: int = Field(..., description="配置ID")
    createTime: str | None = Field(default=None, description="创建时间")


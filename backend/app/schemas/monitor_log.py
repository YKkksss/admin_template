"""监控/审计日志 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class IdsPayload(BaseModel):
    ids: list[int] = Field(default_factory=list, description="ID 列表")


class OperationLogOut(BaseModel):
    id: int = Field(..., description="日志ID")
    userId: int | None = Field(default=None, description="用户ID")
    username: str | None = Field(default=None, description="用户名")
    module: str | None = Field(default=None, description="操作模块")
    action: str | None = Field(default=None, description="操作类型")
    method: str = Field(..., description="请求方法")
    url: str = Field(..., description="请求URL")
    ip: str | None = Field(default=None, description="IP地址")
    requestData: str | None = Field(default=None, description="请求数据（脱敏后）")
    responseData: str | None = Field(default=None, description="响应数据（摘要）")
    status: int | None = Field(default=None, description="状态：0失败 1成功")
    duration: int | None = Field(default=None, description="耗时(ms)")
    createTime: str | None = Field(default=None, description="创建时间")


class LoginLogOut(BaseModel):
    id: int = Field(..., description="日志ID")
    userId: int | None = Field(default=None, description="用户ID")
    username: str | None = Field(default=None, description="用户名")
    ip: str | None = Field(default=None, description="IP地址")
    location: str | None = Field(default=None, description="登录地点")
    browser: str | None = Field(default=None, description="浏览器")
    os: str | None = Field(default=None, description="操作系统")
    status: int | None = Field(default=None, description="状态：0失败 1成功")
    message: str | None = Field(default=None, description="消息")
    createTime: str | None = Field(default=None, description="创建时间")


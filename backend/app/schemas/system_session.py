from pydantic import BaseModel, Field


class SystemSessionOut(BaseModel):
    """在线会话（列表展示）。"""

    id: int = Field(..., description="会话ID")
    username: str = Field(..., description="用户名")
    ip: str | None = Field(default=None, description="登录IP")
    browser: str | None = Field(default=None, description="浏览器")
    os: str | None = Field(default=None, description="操作系统")
    loginTime: str | None = Field(default=None, description="登录时间")
    lastActiveTime: str | None = Field(default=None, description="最后活跃时间")
    expireTime: str | None = Field(default=None, description="过期时间")
    status: int = Field(default=1, description="状态：1在线 0下线")
    revokeReason: str | None = Field(default=None, description="下线原因")
    isCurrent: bool = Field(default=False, description="是否当前会话")


class BatchKickRequest(BaseModel):
    ids: list[int] = Field(default_factory=list, description="会话ID列表")
    reason: str | None = Field(default=None, description="下线原因")


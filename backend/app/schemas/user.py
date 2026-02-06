from pydantic import BaseModel, Field


class CurrentUser(BaseModel):
    """从 Token 解析得到的最小用户信息（用于鉴权与权限判断）。"""

    username: str = Field(..., description="用户名")
    roles: list[str] = Field(default_factory=list, description="角色标识列表")
    jti: str | None = Field(default=None, description="Token ID（用于会话校验）")


class UserInfo(BaseModel):
    """返回给前端的用户信息结构。"""

    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    realName: str = Field(..., description="真实姓名")
    roles: list[str] = Field(default_factory=list, description="角色标识列表")
    homePath: str | None = Field(default=None, description="首页路径")
    avatar: str | None = Field(default=None, description="头像")
    introduction: str | None = Field(default=None, description="个人简介")


class UserProfileUpdate(BaseModel):
    """当前登录用户的基础信息更新。"""

    realName: str | None = Field(default=None, min_length=1, max_length=50, description="真实姓名")
    avatar: str | None = Field(default=None, max_length=255, description="头像")
    homePath: str | None = Field(default=None, max_length=255, description="首页路径")
    introduction: str | None = Field(default=None, max_length=255, description="个人简介")


class UserChangePassword(BaseModel):
    """当前登录用户修改密码。"""

    oldPassword: str = Field(..., min_length=1, description="旧密码")
    newPassword: str = Field(..., min_length=6, description="新密码（最少 6 位）")

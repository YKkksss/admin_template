from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求。"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应数据。"""

    accessToken: str = Field(..., description="访问令牌")


class RegisterRequest(BaseModel):
    """注册请求。"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class RegisterResponse(BaseModel):
    """注册响应数据。"""

    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")

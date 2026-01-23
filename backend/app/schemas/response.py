"""统一响应模型。"""

from __future__ import annotations

import time

from pydantic import BaseModel, Field


class ApiResponse[T](BaseModel):
    """
    统一响应格式。

    约定：
    - code：业务状态码，0 表示成功，非 0 表示失败（与前端拦截器保持一致）。
    - message：提示信息。
    - error：错误信息（成功时为 null）。前端会优先读取该字段用于提示。
    - data：实际返回数据。
    - timestamp：服务端时间戳（秒）。
    """

    code: int = Field(default=0, description="业务状态码：0成功，非0失败")
    message: str = Field(default="ok", description="提示信息")
    error: str | None = Field(default=None, description="错误信息（成功时为 null）")
    data: T | None = Field(default=None, description="响应数据")
    timestamp: int = Field(default_factory=lambda: int(time.time()), description="时间戳（秒）")


def ok[T](data: T, message: str = "ok") -> ApiResponse[T]:
    """成功响应快捷方法。"""

    return ApiResponse(code=0, data=data, message=message, error=None)


def fail(message: str, code: int = -1, data: object | None = None) -> ApiResponse[object]:
    """失败响应快捷方法。"""

    return ApiResponse(code=code, data=data, message=message, error=message)

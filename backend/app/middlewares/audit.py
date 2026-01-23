"""审计日志中间件。"""

from __future__ import annotations

import json
from typing import Any

from fastapi import Request

from app.models.log import OperationLog
from app.services.auth import auth_service

_SENSITIVE_KEYS = {
    "password",
    "oldPassword",
    "newPassword",
    "confirmPassword",
    "secret",
    "token",
    "refreshToken",
}


def _mask_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        masked: dict[str, Any] = {}
        for k, v in value.items():
            if k in _SENSITIVE_KEYS:
                masked[k] = "***"
            else:
                masked[k] = _mask_sensitive(v)
        return masked
    if isinstance(value, list):
        return [_mask_sensitive(v) for v in value]
    return value


def _derive_action(method: str) -> str:
    m = method.upper()
    if m == "GET":
        return "query"
    if m == "POST":
        return "create"
    if m in {"PUT", "PATCH"}:
        return "update"
    if m == "DELETE":
        return "delete"
    return m.lower()


def _derive_module(path: str) -> str | None:
    # /api/v1/system/user/list -> system.user
    parts = [p for p in path.strip("/").split("/") if p]
    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "v1":
        return ".".join(parts[2:4]) if len(parts) >= 4 else parts[2]
    return None


async def try_write_operation_log(
    *,
    request: Request,
    status_code: int,
    duration_ms: int,
    response_summary: str | None = None,
) -> None:
    """
    写入操作日志（失败不影响主流程）。

    说明：
    - 默认仅记录非 GET 请求（减少噪声与写入压力）。
    - 对登录/注册等包含敏感信息的接口做跳过。
    """

    method = request.method.upper()
    if method == "GET":
        return

    path = request.url.path
    if path.startswith("/api/v1/auth/"):
        return
    if path.startswith("/api/v1/ws"):
        return

    username: str | None = None
    try:
        auth = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
            current = auth_service.parse_access_token(token)
            if current:
                username = current.username
    except Exception:
        username = None

    ip = request.client.host if request.client else None

    request_payload: dict[str, Any] = {}
    try:
        if request.query_params:
            request_payload["query"] = dict(request.query_params)
    except Exception:
        pass

    try:
        content_type = (request.headers.get("content-type") or "").lower()
        if "application/json" in content_type:
            body = await request.body()
            if body:
                data = json.loads(body.decode("utf-8"))
                request_payload["body"] = _mask_sensitive(data)
    except Exception:
        # 解析失败不影响主流程
        pass

    request_data = None
    try:
        if request_payload:
            request_data = json.dumps(request_payload, ensure_ascii=False)[:8000]
    except Exception:
        request_data = None

    try:
        await OperationLog.create(
            username=username,
            module=_derive_module(path),
            action=_derive_action(method),
            method=method,
            url=path,
            ip=ip,
            request_data=request_data,
            response_data=(response_summary or None),
            status=1 if status_code < 400 else 0,
            duration=duration_ms,
        )
    except Exception:
        # 日志写入失败不应影响正常业务
        return

"""
FastAPI 应用入口。

启动命令（开发模式）：
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.middlewares.audit import try_write_operation_log
from app.schemas.response import fail


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_request, exc: StarletteHTTPException):  # noqa: ANN001
        """
        统一 HTTP 异常响应格式，兼容前端的错误提示逻辑。

        前端会优先读取响应体中的 `error` 或 `message` 字段进行提示。
        """

        if isinstance(exc.detail, str):
            payload = fail(exc.detail)
        else:
            payload = fail("请求失败", data=exc.detail)

        return JSONResponse(
            status_code=exc.status_code,
            content={**payload.model_dump(), "timestamp": int(time.time())},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request, exc: RequestValidationError):  # noqa: ANN001
        payload = fail("请求参数校验失败", data=exc.errors())
        return JSONResponse(
            status_code=422,
            content={**payload.model_dump(), "timestamp": int(time.time())},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request, exc: Exception):  # noqa: ANN001
        message = str(exc) if settings.DEBUG else "服务器内部错误"
        payload = fail(message)
        return JSONResponse(
            status_code=500,
            content={**payload.model_dump(), "timestamp": int(time.time())},
        )

    allow_origins = settings.CORS_ORIGINS or ["*"]
    # CORS 规范下，Access-Control-Allow-Origin 不能在携带凭据时使用 "*"
    # 这里当允许任意来源时，默认关闭 allow_credentials，避免浏览器直接拦截
    allow_credentials = "*" not in allow_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def audit_log_middleware(request: Request, call_next):  # noqa: ANN001
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        await try_write_operation_log(
            request=request,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response

    app.include_router(api_router)

    # 数据库初始化（如果连接配置不正确会在启动期暴露问题）
    init_db(app)

    return app


app = create_app()

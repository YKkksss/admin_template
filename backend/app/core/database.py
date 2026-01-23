"""数据库配置与初始化（Tortoise ORM）。"""

from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.core.config import settings
from app.core.seed import seed_superuser

_POSTGRES_DB_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")


def normalize_database_url(url: str) -> str:
    """
    规范化数据库连接串，避免不同写法导致的驱动识别问题。

    说明：
    - 文档示例中可能出现 `postgresql+asyncpg://`（更偏 SQLAlchemy 风格），
      这里统一转为 tortoise 支持的格式。
    """

    if url.startswith("postgresql+asyncpg://"):
        return "postgres://" + url.removeprefix("postgresql+asyncpg://")
    if url.startswith("mysql+aiomysql://"):
        return "mysql://" + url.removeprefix("mysql+aiomysql://")
    return url


async def ensure_database_exists() -> None:
    """
    确保数据库存在（仅对 PostgreSQL 生效）。

    目标：
    - 当 `DATABASE_URL` 指向的数据库不存在时，自动创建数据库。
    - 便于首次部署/联调快速落地环境。
    """

    db_url = normalize_database_url(settings.DATABASE_URL)
    parsed = urlparse(db_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        return

    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    user = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    database = (parsed.path or "").lstrip("/")

    if not user or not database:
        raise RuntimeError("PostgreSQL 配置不完整，请检查 DATABASE_URL。")

    if not _POSTGRES_DB_NAME_RE.fullmatch(database):
        raise RuntimeError(
            "数据库名包含非法字符，仅允许字母/数字/下划线，请检查 DATABASE_URL。",
        )

    # 优先使用 postgres 管理库，如果不可用再尝试 template1
    admin_databases = ("postgres", "template1")
    last_error: Exception | None = None

    for admin_db in admin_databases:
        try:
            import asyncpg

            conn = await asyncpg.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database=admin_db,
                ssl=bool(getattr(settings, "POSTGRES_SSL", False)),
                timeout=10,
            )
            try:
                exists = await conn.fetchval(
                    "SELECT 1 FROM pg_database WHERE datname = $1",
                    database,
                )
                if not exists:
                    try:
                        await conn.execute(f'CREATE DATABASE "{database}"')
                    except asyncpg.DuplicateDatabaseError:
                        # 并发启动时可能出现竞态，数据库已被其他实例创建
                        pass
            finally:
                await conn.close()
            return
        except Exception as exc:  # noqa: BLE001 - 需要兜底并给出友好错误
            last_error = exc
            continue

    raise RuntimeError(
        f"无法连接到 PostgreSQL({host}:{port}) 创建数据库 {database}，"
        "请确认网络可达、账号权限以及 postgres/template1 管理库可用。",
    ) from last_error


def build_tortoise_config() -> dict:
    db_url = normalize_database_url(settings.DATABASE_URL)
    parsed = urlparse(db_url)

    # 明确指定 asyncpg 连接参数，避免环境差异导致的 SSL 协商问题
    connection: str | dict = db_url
    if parsed.scheme in {"postgres", "postgresql"}:
        connection = {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 5432,
                "user": unquote(parsed.username or ""),
                "password": unquote(parsed.password or ""),
                "database": (parsed.path or "").lstrip("/"),
                "ssl": bool(getattr(settings, "POSTGRES_SSL", False)),
            },
        }

    return {
        "connections": {"default": connection},
        "apps": {
            "models": {
                "models": [
                    "app.models.user",
                    "app.models.role",
                    "app.models.menu",
                    "app.models.dept",
                    "app.models.notice",
                    "app.models.dict",
                    "app.models.config",
                    "app.models.log",
                    "aerich.models",
                ],
                "default_connection": "default",
            },
        },
        "use_tz": True,
        "timezone": "Asia/Shanghai",
    }


# 提供给 Aerich 的全局常量（aerich.ini 会引用该路径）
TORTOISE_ORM = build_tortoise_config()


def init_db(app: FastAPI) -> None:
    """
    将 Tortoise ORM 注册到 FastAPI 生命周期中。

    说明：
    - 生产环境建议使用 Aerich 进行迁移，不建议依赖 `generate_schemas=True`。
    """

    # 先确保数据库存在，再让 Tortoise 在启动阶段建立连接
    app.add_event_handler("startup", ensure_database_exists)

    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=False,
        add_exception_handlers=settings.DEBUG,
    )

    # Tortoise 初始化完成后，进行开发期数据播种（如超级管理员账号）
    app.add_event_handler("startup", seed_superuser)

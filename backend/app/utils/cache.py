"""Redis 缓存工具（占位实现）。"""

from __future__ import annotations

from app.core.config import settings


def get_redis_url() -> str | None:
    """获取 Redis 连接地址（未配置则返回 None）。"""

    return settings.REDIS_URL

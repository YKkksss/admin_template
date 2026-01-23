"""消息通知 WebSocket 管理器（开发期单进程实现）。"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict

from fastapi import WebSocket


class NoticeWsManager:
    """
    WebSocket 连接管理器。

    说明：
    - 当前实现为内存态，适用于单进程/单实例部署。
    - 如果未来需要多实例扩展，可改造为 Redis PubSub / MQ 广播。
    """

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, username: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[username].add(websocket)

    async def disconnect(self, username: str, websocket: WebSocket) -> None:
        async with self._lock:
            conns = self._connections.get(username)
            if not conns:
                return
            conns.discard(websocket)
            if not conns:
                self._connections.pop(username, None)

    async def send_to_user(self, username: str, event: dict) -> None:
        async with self._lock:
            targets = list(self._connections.get(username, set()))

        if not targets:
            return

        for ws in targets:
            try:
                await ws.send_json(event)
            except Exception:
                # 发送失败通常意味着连接已断开，交由 websocket 断开流程清理
                continue

    async def broadcast_users(self, usernames: list[str], event: dict) -> None:
        for username in usernames:
            await self.send_to_user(username, event)

    @staticmethod
    def build_event(event: str, data: dict | None = None) -> dict:
        return {
            "event": event,
            "timestamp": int(time.time()),
            "data": data or {},
        }


notice_ws_manager = NoticeWsManager()


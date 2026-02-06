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
        # username -> jti -> websockets
        self._connections: dict[str, dict[str, set[WebSocket]]] = defaultdict(
            lambda: defaultdict(set),
        )
        self._lock = asyncio.Lock()

    async def connect(self, username: str, jti: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[username][jti].add(websocket)

    async def disconnect(self, username: str, jti: str, websocket: WebSocket) -> None:
        async with self._lock:
            user_conns = self._connections.get(username)
            if not user_conns:
                return
            conns = user_conns.get(jti)
            if not conns:
                return
            conns.discard(websocket)
            if not conns:
                user_conns.pop(jti, None)
            if not user_conns:
                self._connections.pop(username, None)

    async def send_to_user(self, username: str, event: dict) -> None:
        async with self._lock:
            user_conns = self._connections.get(username, {})
            targets: list[WebSocket] = []
            for conns in user_conns.values():
                targets.extend(list(conns))

        if not targets:
            return

        for ws in targets:
            try:
                await ws.send_json(event)
            except Exception:
                # 发送失败通常意味着连接已断开，交由 websocket 断开流程清理
                continue

    async def send_to_session(self, username: str, jti: str, event: dict) -> None:
        """仅向指定会话（同一 token 的多标签页）推送事件。"""

        async with self._lock:
            targets = list(self._connections.get(username, {}).get(jti, set()))

        if not targets:
            return

        for ws in targets:
            try:
                await ws.send_json(event)
            except Exception:
                continue

    async def broadcast_users(self, usernames: list[str], event: dict) -> None:
        for username in usernames:
            await self.send_to_user(username, event)

    async def broadcast_sessions(self, sessions: list[tuple[str, str]], event: dict) -> None:
        for username, jti in sessions:
            await self.send_to_session(username, jti, event)

    @staticmethod
    def build_event(event: str, data: dict | None = None) -> dict:
        return {
            "event": event,
            "timestamp": int(time.time()),
            "data": data or {},
        }


notice_ws_manager = NoticeWsManager()

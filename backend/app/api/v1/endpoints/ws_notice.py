from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.services.auth import auth_service
from app.ws.notice import notice_ws_manager

router = APIRouter()


@router.websocket("/ws/notice")
async def notice_ws(websocket: WebSocket, token: str = Query(default="")):
    """
    消息通知 WebSocket。

    约定：
    - 前端通过 query 传入 token：/ws/notice?token=xxx
    - token 解析失败则直接关闭连接
    """

    await websocket.accept()

    if token.startswith("Bearer "):
        token = token.removeprefix("Bearer ").strip()

    current_user = auth_service.parse_access_token(token)
    if not current_user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await notice_ws_manager.connect(current_user.username, websocket)

    try:
        while True:
            # 当前阶段仅用于保持连接；后续可扩展：客户端订阅、心跳、回执等
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await notice_ws_manager.disconnect(current_user.username, websocket)


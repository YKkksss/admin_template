"""会话服务：在线用户、单端登录、强制下线。"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.config import settings
from app.models.config import Config
from app.models.session import UserSession
from app.models.user import User
from app.utils.user_agent import parse_browser, parse_os
from app.ws.notice import notice_ws_manager

_VALID_LOGIN_MODES = {"single", "multi"}


def _now() -> datetime:
    return datetime.now(UTC)


def _normalize_login_mode(value: str | None) -> str | None:
    mode = (value or "").strip().lower()
    return mode if mode in _VALID_LOGIN_MODES else None


class SessionService:
    async def get_login_mode(self) -> str:
        """
        获取登录模式。

        优先级：
        1) 环境变量 SESSION_LOGIN_MODE
        2) 系统配置 auth.login.mode
        3) 默认 multi
        """

        env_mode = _normalize_login_mode(getattr(settings, "SESSION_LOGIN_MODE", None))
        if env_mode:
            return env_mode

        cfg = await Config.get_or_none(key="auth.login.mode", status=1)
        db_mode = _normalize_login_mode(cfg.value if cfg else None)
        return db_mode or "multi"

    async def create_session(
        self,
        *,
        user: User,
        jti: str,
        expires_at: datetime | None,
        ip: str | None,
        user_agent: str | None,
    ) -> UserSession:
        """
        创建会话记录。

        说明：
        - single 模式会撤销该用户的其他在线会话，并通过 WS 发送踢下线事件。
        """

        now = _now()
        mode = await self.get_login_mode()

        if mode == "single":
            revoked_sessions = (
                await UserSession.filter(user_id=user.id, status=1).exclude(jti=jti).all()
            )
            if revoked_sessions:
                revoke_ids = [s.id for s in revoked_sessions]
                await UserSession.filter(id__in=revoke_ids, status=1).update(
                    status=0,
                    revoked_at=now,
                    revoke_reason="账号在其他地方登录，您已被迫下线",
                    revoked_by="system",
                )
                await notice_ws_manager.broadcast_sessions(
                    [(s.username, s.jti) for s in revoked_sessions],
                    notice_ws_manager.build_event(
                        "auth:kickout",
                        {"reason": "账号在其他地方登录，您已被迫下线"},
                    ),
                )

        return await UserSession.create(
            user=user,
            username=user.username,
            jti=jti,
            ip=ip,
            user_agent=user_agent,
            browser=parse_browser(user_agent),
            os=parse_os(user_agent),
            last_seen_at=now,
            expires_at=expires_at,
            status=1,
        )

    async def validate_session(self, *, username: str, jti: str | None) -> tuple[bool, str]:
        """
        校验会话是否有效。

        返回：
        - (True, "ok")：会话有效
        - (False, reason)：会话无效及原因
        """

        if not jti:
            return False, "登录信息无效，请重新登录"

        session = await UserSession.get_or_none(jti=jti, username=username)
        if not session:
            return False, "登录信息无效，请重新登录"

        if session.status != 1:
            return False, session.revoke_reason or "已被强制下线，请重新登录"

        now = _now()
        if session.expires_at and session.expires_at <= now:
            return False, "登录已过期，请重新登录"

        # 更新最后活跃时间（做简单节流，避免每次请求都写库）
        try:
            if not session.last_seen_at or (now - session.last_seen_at).total_seconds() >= 30:
                session.last_seen_at = now
                await session.save(update_fields=["last_seen_at"])
        except Exception:
            # 最后活跃时间写入失败不影响鉴权
            pass

        return True, "ok"

    async def revoke_sessions(
        self,
        *,
        session_ids: list[int],
        revoked_by: str,
        reason: str,
        send_kickout_event: bool = True,
    ) -> int:
        """
        撤销会话（强制下线）。

        返回：实际撤销数量（仅统计从在线 -> 下线的数量）。
        """

        ids = [int(i) for i in session_ids if i]
        if not ids:
            return 0

        sessions = await UserSession.filter(id__in=ids).all()
        if not sessions:
            return 0

        now = _now()
        affected_sessions: list[tuple[str, str]] = []
        revoke_count = 0

        for s in sessions:
            if s.status == 1:
                revoke_count += 1
                affected_sessions.append((s.username, s.jti))

        if revoke_count <= 0:
            return 0

        await UserSession.filter(id__in=ids, status=1).update(
            status=0,
            revoked_at=now,
            revoke_reason=reason,
            revoked_by=revoked_by,
        )

        # 推送踢下线事件（用于前端提示与自动退出）
        if send_kickout_event and affected_sessions:
            await notice_ws_manager.broadcast_sessions(
                affected_sessions,
                notice_ws_manager.build_event(
                    "auth:kickout",
                    {"reason": reason},
                ),
            )

        return revoke_count

    async def revoke_by_jti(
        self,
        *,
        username: str,
        jti: str | None,
        revoked_by: str,
        reason: str,
    ) -> bool:
        if not jti:
            return False

        session = await UserSession.get_or_none(jti=jti, username=username)
        if not session:
            return False

        if session.status != 1:
            return True

        await self.revoke_sessions(
            session_ids=[session.id],
            revoked_by=revoked_by,
            reason=reason,
            send_kickout_event=False,
        )
        return True


session_service = SessionService()

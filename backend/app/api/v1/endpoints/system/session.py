from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import require_permissions
from app.models.session import UserSession
from app.schemas.response import ApiResponse, ok
from app.schemas.system_session import BatchKickRequest, SystemSessionOut
from app.schemas.user import CurrentUser
from app.services.data_scope import get_allowed_user_ids
from app.services.session import session_service

router = APIRouter()


def _format_dt(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


@router.get("/list", response_model=ApiResponse[dict])
async def list_sessions(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
    username: str | None = Query(default=None),
    ip: str | None = Query(default=None),
    status_: int | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(require_permissions("System:Session:List")),
):
    """在线用户/会话列表（分页）。"""

    qs = UserSession.all()
    allowed_user_ids = await get_allowed_user_ids(current_user)
    if allowed_user_ids is not None:
        qs = qs.filter(user_id__in=list(allowed_user_ids) or [0])
    if username:
        qs = qs.filter(username__icontains=username)
    if ip:
        qs = qs.filter(ip__icontains=ip)
    if status_ in (0, 1):
        qs = qs.filter(status=status_)

    total = await qs.count()
    records = await qs.order_by("-id").offset((page - 1) * pageSize).limit(pageSize)

    now = datetime.now(UTC)
    items: list[SystemSessionOut] = []
    for s in records:
        expired = bool(s.expires_at and s.expires_at <= now)
        effective_status = 0 if s.status != 1 or expired else 1
        revoke_reason = s.revoke_reason
        if expired and not revoke_reason:
            revoke_reason = "登录已过期"

        items.append(
            SystemSessionOut(
                id=s.id,
                username=s.username,
                ip=s.ip,
                browser=s.browser,
                os=s.os,
                loginTime=_format_dt(s.created_at),
                lastActiveTime=_format_dt(s.last_seen_at),
                expireTime=_format_dt(s.expires_at),
                status=effective_status,
                revokeReason=revoke_reason,
                isCurrent=(s.username == current_user.username and s.jti == current_user.jti),
            ),
        )

    return ok({"items": items, "total": total})


@router.delete("/{session_id}", response_model=ApiResponse[bool])
async def kick_session(
    session_id: int,
    reason: str | None = Query(default=None),
    current_user: CurrentUser = Depends(require_permissions("System:Session:Kick")),
):
    """强制下线指定会话。"""

    session = await UserSession.get_or_none(id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    allowed_user_ids = await get_allowed_user_ids(current_user)
    if allowed_user_ids is not None and int(session.user_id) not in allowed_user_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

    kick_reason = (reason or "").strip() or "管理员强制下线"
    await session_service.revoke_sessions(
        session_ids=[session_id],
        revoked_by=current_user.username,
        reason=kick_reason,
    )
    return ok(True)


@router.post("/batch-kick", response_model=ApiResponse[int])
async def batch_kick_sessions(
    payload: BatchKickRequest,
    current_user: CurrentUser = Depends(require_permissions("System:Session:Kick")),
):
    """批量强制下线会话。"""

    allowed_user_ids = await get_allowed_user_ids(current_user)
    if allowed_user_ids is not None:
        sessions = await UserSession.filter(id__in=payload.ids).all()
        if any(int(s.user_id) not in allowed_user_ids for s in sessions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

    reason = (payload.reason or "").strip() or "管理员强制下线"
    count = await session_service.revoke_sessions(
        session_ids=payload.ids,
        revoked_by=current_user.username,
        reason=reason,
    )
    return ok(count)

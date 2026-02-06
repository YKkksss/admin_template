from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import require_permissions
from app.models.log import LoginLog
from app.schemas.monitor_log import IdsPayload, LoginLogOut
from app.schemas.response import ApiResponse, ok
from app.schemas.user import CurrentUser
from app.services.data_scope import get_allowed_user_ids

router = APIRouter()


def _format_dt(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


@router.get("/list", response_model=ApiResponse[dict])
async def list_login_logs(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
    username: str | None = Query(default=None),
    status_: int | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(require_permissions("Monitor:LoginLog:List")),
):
    """获取登录日志列表（分页）。"""

    qs = LoginLog.all()
    allowed_user_ids = await get_allowed_user_ids(current_user)
    if allowed_user_ids is not None:
        qs = qs.filter(user_id__in=list(allowed_user_ids) or [0])
    if username:
        qs = qs.filter(username__icontains=username)
    if status_ in (0, 1):
        qs = qs.filter(status=status_)

    total = await qs.count()
    records = await qs.order_by("-id").offset((page - 1) * pageSize).limit(pageSize)

    items: list[LoginLogOut] = []
    for rec in records:
        items.append(
            LoginLogOut(
                id=rec.id,
                userId=rec.user_id,
                username=rec.username,
                ip=rec.ip,
                location=rec.location,
                browser=rec.browser,
                os=rec.os,
                status=rec.status,
                message=rec.message,
                createTime=_format_dt(rec.created_at),
            ),
        )

    return ok({"items": items, "total": total})


@router.delete("/{log_id}", response_model=ApiResponse[bool])
async def delete_login_log(
    log_id: int,
    current_user: CurrentUser = Depends(require_permissions("Monitor:LoginLog:Delete")),
):
    """删除单条登录日志。"""

    rec = await LoginLog.get_or_none(id=log_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日志不存在")
    allowed_user_ids = await get_allowed_user_ids(current_user)
    if allowed_user_ids is not None and (
        rec.user_id is None or int(rec.user_id) not in allowed_user_ids
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    await rec.delete()
    return ok(True)


@router.post("/batch-delete", response_model=ApiResponse[bool])
async def batch_delete_login_logs(
    payload: IdsPayload,
    current_user: CurrentUser = Depends(require_permissions("Monitor:LoginLog:Delete")),
):
    """批量删除登录日志。"""

    ids = [int(i) for i in (payload.ids or []) if int(i) > 0]
    if not ids:
        return ok(True)

    allowed_user_ids = await get_allowed_user_ids(current_user)
    if allowed_user_ids is not None:
        records = await LoginLog.filter(id__in=ids).all()
        if any(r.user_id is None or int(r.user_id) not in allowed_user_ids for r in records):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

    await LoginLog.filter(id__in=ids).delete()
    return ok(True)


@router.post("/clear", response_model=ApiResponse[bool])
async def clear_login_logs(
    current_user: CurrentUser = Depends(require_permissions("Monitor:LoginLog:Delete")),
):
    """清空登录日志（危险操作）。"""

    allowed_user_ids = await get_allowed_user_ids(current_user)
    if allowed_user_ids is None:
        await LoginLog.all().delete()
    else:
        await LoginLog.filter(user_id__in=list(allowed_user_ids) or [0]).delete()
    return ok(True)

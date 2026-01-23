from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from tortoise.expressions import Q

from app.api.v1.deps import get_current_user
from app.models.notice import Notice, UserNotice
from app.models.user import User
from app.schemas.notice import NoticeDetail, NoticeIdsRequest, NoticeInboxItem, format_dt
from app.schemas.response import ApiResponse, ok
from app.schemas.user import CurrentUser

router = APIRouter()


def _build_item(un: UserNotice, *, notice: Notice) -> NoticeInboxItem:
    return NoticeInboxItem(
        id=un.id,
        title=notice.title,
        message=notice.message,
        type=notice.type,
        link=notice.link,
        isRead=bool(un.is_read),
        createTime=format_dt(un.created_at) or "",
        readTime=format_dt(un.read_at),
    )


def _build_detail(un: UserNotice, *, notice: Notice) -> NoticeDetail:
    return NoticeDetail(
        id=un.id,
        title=notice.title,
        message=notice.message,
        content=notice.content,
        type=notice.type,
        link=notice.link,
        isRead=bool(un.is_read),
        createTime=format_dt(un.created_at) or "",
        readTime=format_dt(un.read_at),
    )


@router.get("/bell", response_model=ApiResponse[list[NoticeInboxItem]])
async def get_bell_notices(current_user: CurrentUser = Depends(get_current_user)):
    """获取铃铛未读消息列表（仅返回未读且未隐藏的消息）。"""

    user = await User.get_or_none(username=current_user.username, is_active=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    qs = (
        UserNotice.filter(user_id=user.id, is_read=False, bell_hidden=False)
        .select_related("notice")
        .order_by("-created_at", "-id")
    )
    user_notices = await qs.all()

    items: list[NoticeInboxItem] = []
    for un in user_notices:
        if not un.notice:
            continue
        items.append(_build_item(un, notice=un.notice))

    return ok(items)


@router.post("/bell/clear", response_model=ApiResponse[bool])
async def clear_bell(current_user: CurrentUser = Depends(get_current_user)):
    """清空铃铛列表：将当前用户铃铛内消息全部隐藏（不改变已读状态）。"""

    user = await User.get_or_none(username=current_user.username, is_active=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    now = datetime.now().astimezone()
    await UserNotice.filter(user_id=user.id, bell_hidden=False).update(
        bell_hidden=True,
        bell_hidden_at=now,
    )
    return ok(True)


@router.post("/bell/read-all", response_model=ApiResponse[bool])
async def read_all_bell(current_user: CurrentUser = Depends(get_current_user)):
    """铃铛全部已读：仅标记铃铛当前展示的未读消息为已读。"""

    user = await User.get_or_none(username=current_user.username, is_active=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    now = datetime.now().astimezone()
    await UserNotice.filter(user_id=user.id, is_read=False, bell_hidden=False).update(
        is_read=True,
        read_at=now,
    )
    return ok(True)


@router.get("/inbox", response_model=ApiResponse[dict])
async def inbox_list(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
    keyword: str | None = Query(default=None),
    readStatus: str = Query(default="all"),
    type_: int | None = Query(default=None, alias="type"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """消息收件箱列表（分页，按最新优先）。"""

    user = await User.get_or_none(username=current_user.username, is_active=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    qs = UserNotice.filter(user_id=user.id).select_related("notice")

    if readStatus == "unread":
        qs = qs.filter(is_read=False)
    elif readStatus == "read":
        qs = qs.filter(is_read=True)

    if type_ in {1, 2, 3}:
        qs = qs.filter(notice__type=type_)

    if keyword:
        qs = qs.filter(
            Q(notice__title__icontains=keyword) | Q(notice__message__icontains=keyword),
        )

    total = await qs.count()
    rows = await qs.order_by("-created_at", "-id").offset((page - 1) * pageSize).limit(pageSize)

    items: list[NoticeInboxItem] = []
    for un in rows:
        if not un.notice:
            continue
        items.append(_build_item(un, notice=un.notice))

    return ok({"items": items, "total": total})


@router.get("/inbox/{user_notice_id}", response_model=ApiResponse[NoticeDetail])
async def inbox_detail(
    user_notice_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """获取消息详情（用于抽屉展示）。"""

    user = await User.get_or_none(username=current_user.username, is_active=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    un = await UserNotice.get_or_none(id=user_notice_id, user_id=user.id).select_related("notice")
    if not un or not un.notice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")

    return ok(_build_detail(un, notice=un.notice))


@router.post("/inbox/{user_notice_id}/read", response_model=ApiResponse[bool])
async def mark_read(
    user_notice_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """标记单条消息为已读。"""

    user = await User.get_or_none(username=current_user.username, is_active=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    un = await UserNotice.get_or_none(id=user_notice_id, user_id=user.id)
    if not un:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")

    if not un.is_read:
        now = datetime.now().astimezone()
        un.is_read = True
        un.read_at = now
        await un.save()

    return ok(True)


@router.delete("/inbox/{user_notice_id}", response_model=ApiResponse[bool])
async def delete_one(
    user_notice_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    """删除单条消息（仅删除当前用户的收件箱记录）。"""

    user = await User.get_or_none(username=current_user.username, is_active=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    deleted = await UserNotice.filter(id=user_notice_id, user_id=user.id).delete()
    if deleted == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    return ok(True)


@router.post("/inbox/delete-batch", response_model=ApiResponse[int])
async def delete_batch(
    payload: NoticeIdsRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """批量删除消息（仅删除当前用户的收件箱记录）。"""

    user = await User.get_or_none(username=current_user.username, is_active=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    ids = [int(i) for i in payload.ids]
    deleted = await UserNotice.filter(user_id=user.id, id__in=ids).delete()
    return ok(int(deleted))

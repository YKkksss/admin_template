from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from tortoise.expressions import Q
from tortoise.functions import Count

from app.api.v1.deps import require_permissions
from app.models.dept import Dept
from app.models.notice import Notice, UserNotice
from app.models.user import User
from app.schemas.notice import NoticeOutboxDetail, NoticeOutboxItem, NoticeSendRequest, format_dt
from app.schemas.response import ApiResponse, ok
from app.schemas.user import CurrentUser
from app.ws.notice import notice_ws_manager

router = APIRouter()


async def _expand_dept_ids(dept_ids: set[int]) -> set[int]:
    """
    递归展开部门 ID（包含子部门）。

    说明：
    - 当前使用 Python 侧遍历，适合中小规模数据；
    - 若未来部门规模很大，可改为递归 CTE 在数据库侧完成。
    """

    if not dept_ids:
        return set()

    rows = await Dept.all().values("id", "parent_id")
    children: dict[int, list[int]] = defaultdict(list)
    for row in rows:
        pid = row.get("parent_id")
        if pid is None:
            continue
        children[int(pid)].append(int(row["id"]))

    expanded: set[int] = set(int(d) for d in dept_ids)
    queue = list(expanded)
    while queue:
        current = queue.pop(0)
        for child_id in children.get(current, []):
            if child_id in expanded:
                continue
            expanded.add(child_id)
            queue.append(child_id)

    return expanded


def _get_send_scope(notice: Notice) -> str:
    if bool(getattr(notice, "send_all", False)):
        return "all"

    dept_ids = notice.dept_ids if isinstance(notice.dept_ids, list) else []
    user_ids = notice.user_ids if isinstance(notice.user_ids, list) else []

    if dept_ids and user_ids:
        return "mixed"
    if dept_ids:
        return "dept"
    if user_ids:
        return "user"
    return "unknown"


@router.post("/send", response_model=ApiResponse[int])
async def send_notice(
    payload: NoticeSendRequest,
    current_user: CurrentUser = Depends(require_permissions("System:Notice:Send")),
):
    """发送站内消息（管理员接口）。"""

    if not payload.sendAll and not payload.deptIds and not payload.userIds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请指定接收用户/部门或选择发送给全部用户",
        )

    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="标题不能为空")

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="内容不能为空")

    summary = (payload.message or "").strip()
    if not summary:
        summary = content.replace("\r", " ").replace("\n", " ").strip()
        summary = summary[:200] if len(summary) > 200 else summary

    sender = await User.get_or_none(username=current_user.username, is_active=True)
    if not sender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="发布人不存在")

    users: list[User] = []
    target_user_ids: set[int] = set()

    if payload.sendAll:
        users = await User.filter(is_active=True).all()
        target_user_ids = {int(u.id) for u in users}
    else:
        selected_user_ids = {int(i) for i in payload.userIds}
        selected_dept_ids = {int(i) for i in payload.deptIds}

        if selected_dept_ids:
            dept_rows = await Dept.filter(id__in=sorted(selected_dept_ids)).values_list(
                "id",
                flat=True,
            )
            existing_dept_ids = {int(i) for i in dept_rows}
            missing = sorted(selected_dept_ids - existing_dept_ids)
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"接收部门不存在：{missing}",
                )

            expanded_dept_ids = await _expand_dept_ids(selected_dept_ids)
            dept_users = await User.filter(
                is_active=True,
                dept_id__in=sorted(expanded_dept_ids),
            ).all()
            target_user_ids.update({int(u.id) for u in dept_users})

        if selected_user_ids:
            explicit_users = await User.filter(
                is_active=True,
                id__in=sorted(selected_user_ids),
            ).all()
            if len(explicit_users) != len(selected_user_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="接收用户不存在或已禁用",
                )
            target_user_ids.update({int(u.id) for u in explicit_users})

        if target_user_ids:
            users = await User.filter(is_active=True, id__in=sorted(target_user_ids)).all()

    if not users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有可发送的接收用户")

    dept_ids_to_store = sorted({int(i) for i in payload.deptIds}) or None
    user_ids_to_store = sorted({int(i) for i in payload.userIds}) or None

    notice = await Notice.create(
        title=title,
        message=summary,
        content=content,
        type=payload.type,
        link=payload.link,
        creator_id=int(sender.id),
        send_all=bool(payload.sendAll),
        dept_ids=dept_ids_to_store,
        user_ids=user_ids_to_store,
    )

    mappings = [
        UserNotice(user_id=u.id, notice_id=notice.id, is_read=False, bell_hidden=False)
        for u in users
    ]
    await UserNotice.bulk_create(mappings)

    usernames = [u.username for u in users if u.username]
    await notice_ws_manager.broadcast_users(
        usernames,
        notice_ws_manager.build_event("notice:new", {"count": len(usernames)}),
    )

    return ok(len(users))


@router.get("/targets/depts", response_model=ApiResponse[list[dict]])
async def list_notice_target_depts(_user=Depends(require_permissions("System:Notice:Send"))):
    """获取可选部门树（用于消息发布范围选择）。"""

    depts = await Dept.all().order_by("id")
    if not depts:
        return ok([])  # type: ignore[arg-type]

    nodes: dict[int, dict] = {}
    roots: list[dict] = []

    for dept in depts:
        nodes[int(dept.id)] = {
            "id": int(dept.id),
            "pid": int(dept.parent_id or 0),
            "name": dept.name,
            "children": [],
        }

    for dept in depts:
        node = nodes[int(dept.id)]
        pid = int(dept.parent_id or 0)
        if pid and pid in nodes:
            nodes[pid]["children"].append(node)
        else:
            roots.append(node)

    return ok(roots)  # type: ignore[arg-type]


@router.get("/targets/users", response_model=ApiResponse[list[dict]])
async def list_notice_target_users(
    keyword: str | None = Query(default=None),
    _user=Depends(require_permissions("System:Notice:Send")),
):
    """获取可选用户列表（用于消息发布范围选择）。"""

    qs = User.filter(is_active=True)
    if keyword and keyword.strip():
        kw = keyword.strip()
        qs = qs.filter(Q(username__icontains=kw) | Q(real_name__icontains=kw))

    users = await qs.order_by("id").limit(1000)
    return ok(
        [
            {
                "id": int(u.id),
                "name": f"{u.real_name}({u.username})",
                "username": u.username,
                "realName": u.real_name,
            }
            for u in users
        ],
    )


@router.get("/outbox", response_model=ApiResponse[dict])
async def outbox_list(
    page: int = 1,
    pageSize: int = 20,
    keyword: str | None = None,
    type_: int | None = None,
    current_user: CurrentUser = Depends(require_permissions("System:Notice:Send")),
):
    """获取“我发布的消息”列表（分页）。"""

    if page < 1:
        page = 1
    if pageSize < 1:
        pageSize = 20
    if pageSize > 200:
        pageSize = 200

    sender = await User.get_or_none(username=current_user.username, is_active=True)
    if not sender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    qs = Notice.filter(creator_id=sender.id).annotate(receiverCount=Count("receivers"))

    if type_ in {1, 2, 3}:
        qs = qs.filter(type=int(type_))

    if keyword:
        kw = keyword.strip()
        if kw:
            qs = qs.filter(Q(title__icontains=kw) | Q(message__icontains=kw))

    total = await qs.count()
    rows = await qs.order_by("-created_at", "-id").offset((page - 1) * pageSize).limit(pageSize)

    items: list[NoticeOutboxItem] = []
    for n in rows:
        receiver_count = int(getattr(n, "receiverCount", 0) or 0)
        items.append(
            NoticeOutboxItem(
                id=int(n.id),
                title=n.title,
                message=n.message,
                type=int(n.type),
                link=n.link,
                sendScope=_get_send_scope(n),
                receiverCount=receiver_count,
                createTime=format_dt(n.created_at) or "",
            ),
        )

    return ok({"items": items, "total": total})


@router.get("/outbox/{notice_id}", response_model=ApiResponse[NoticeOutboxDetail])
async def outbox_detail(
    notice_id: int,
    current_user: CurrentUser = Depends(require_permissions("System:Notice:Send")),
):
    """获取“我发布的消息”详情。"""

    sender = await User.get_or_none(username=current_user.username, is_active=True)
    if not sender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    notice = await Notice.get_or_none(id=notice_id, creator_id=sender.id)
    if not notice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")

    receiver_count = await UserNotice.filter(notice_id=notice.id).count()

    dept_ids = notice.dept_ids if isinstance(notice.dept_ids, list) else []
    user_ids = notice.user_ids if isinstance(notice.user_ids, list) else []

    dept_names: list[str] = []
    if dept_ids:
        depts = await Dept.filter(id__in=[int(i) for i in dept_ids]).all()
        dept_names = [str(d.name) for d in depts]

    user_names: list[str] = []
    if user_ids:
        users = await User.filter(id__in=[int(i) for i in user_ids]).all()
        user_names = [f"{u.real_name}({u.username})" for u in users]

    return ok(
        NoticeOutboxDetail(
            id=int(notice.id),
            title=notice.title,
            message=notice.message,
            content=notice.content,
            type=int(notice.type),
            link=notice.link,
            sendAll=bool(notice.send_all),
            deptIds=[int(i) for i in dept_ids],
            userIds=[int(i) for i in user_ids],
            deptNames=dept_names,
            userNames=user_names,
            sendScope=_get_send_scope(notice),
            receiverCount=int(receiver_count),
            createTime=format_dt(notice.created_at) or "",
        ),
    )

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from tortoise.expressions import Q

from app.api.v1.deps import require_permissions
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.dept import Dept
from app.models.role import Role
from app.models.user import User
from app.schemas.response import ApiResponse, ok
from app.schemas.system_user import (
    SystemUserCreate,
    SystemUserOut,
    SystemUserResetPassword,
    SystemUserUpdate,
)
from app.schemas.user import CurrentUser

router = APIRouter()


def _format_dt(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


async def _is_super_user(user: User) -> bool:
    return await user.roles.filter(code=settings.SUPERUSER_ROLE_CODE).exists()


def _validate_password(password: str) -> None:
    if not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码不能为空")

    if len(password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码长度至少 6 位")

    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码过长（bcrypt 最多 72 字节）",
        )


async def _set_user_roles(user: User, role_ids: list[int], *, actor: CurrentUser) -> None:
    await user.roles.clear()
    if not role_ids:
        role, _ = await Role.get_or_create(code="user", defaults={"name": "普通用户"})
        await user.roles.add(role)
        return

    roles = await Role.filter(id__in=role_ids).all()
    if len(roles) != len(set(role_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色不存在")

    if settings.SUPERUSER_ROLE_CODE not in actor.roles:
        if any(r.code == settings.SUPERUSER_ROLE_CODE for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限授予超级管理员角色",
            )
    await user.roles.add(*roles)


@router.get("/list", response_model=ApiResponse[dict])
async def list_users(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
    username: str | None = Query(default=None),
    realName: str | None = Query(default=None),
    deptId: int | None = Query(default=None),
    status_: str | None = Query(default=None, alias="status"),
    _current_user=Depends(require_permissions("System:User:List")),
):
    """获取用户列表（分页）。"""

    qs = User.all()
    if username:
        qs = qs.filter(username__icontains=username)
    if realName:
        qs = qs.filter(real_name__icontains=realName)
    if deptId:
        qs = qs.filter(dept_id=deptId)
    if status_ in {"0", "1"}:
        qs = qs.filter(is_active=(status_ == "1"))

    total = await qs.count()
    users = (
        await qs.order_by("-id")
        .offset((page - 1) * pageSize)
        .limit(pageSize)
        .prefetch_related("roles", "dept")
    )

    items: list[SystemUserOut] = []
    for user in users:
        roles = list(user.roles) if hasattr(user, "roles") else []
        items.append(
            SystemUserOut(
                id=user.id,
                username=user.username,
                realName=user.real_name,
                status=1 if user.is_active else 0,
                deptId=user.dept_id,
                deptName=user.dept.name if user.dept else None,
                roleIds=[int(r.id) for r in roles],
                roleNames=[str(r.name) for r in roles],
                avatar=user.avatar,
                homePath=user.home_path,
                createTime=_format_dt(user.created_at),
            ),
        )

    return ok({"items": items, "total": total})


@router.post("", response_model=ApiResponse[int])
async def create_user(
    payload: SystemUserCreate,
    current_user: CurrentUser = Depends(require_permissions("System:User:Create")),
):
    """创建用户。"""

    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名不能为空")

    if await User.filter(username=username).exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")

    _validate_password(payload.password)

    dept = None
    if payload.deptId:
        dept = await Dept.get_or_none(id=payload.deptId)
        if not dept:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="部门不存在")

    user = await User.create(
        username=username,
        password_hash=get_password_hash(payload.password),
        real_name=payload.realName,
        is_active=payload.status == 1,
        avatar=payload.avatar,
        home_path=payload.homePath,
        dept=dept,
    )

    await _set_user_roles(user, payload.roleIds, actor=current_user)

    return ok(user.id)


@router.put("/{user_id}", response_model=ApiResponse[bool])
async def update_user(
    user_id: int,
    payload: SystemUserUpdate,
    current_user: CurrentUser = Depends(require_permissions("System:User:Edit")),
):
    """更新用户（支持部分字段）。"""

    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    is_super = await _is_super_user(user)

    if is_super and payload.roleIds is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="超级管理员角色不可修改")

    if "status" in payload.model_fields_set and payload.status is not None:
        if is_super and payload.status == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="超级管理员不可禁用")
        if user.username == current_user.username and payload.status == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能禁用当前登录用户")

        user.is_active = payload.status == 1

    if payload.realName is not None:
        user.real_name = payload.realName

    if "avatar" in payload.model_fields_set:
        user.avatar = payload.avatar
    if "homePath" in payload.model_fields_set:
        user.home_path = payload.homePath

    if "deptId" in payload.model_fields_set:
        if payload.deptId:
            dept = await Dept.get_or_none(id=payload.deptId)
            if not dept:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="部门不存在")
            user.dept = dept
        else:
            user.dept = None

    await user.save()

    if payload.roleIds is not None:
        await _set_user_roles(user, payload.roleIds, actor=current_user)

    return ok(True)


@router.delete("/{user_id}", response_model=ApiResponse[bool])
async def delete_user(
    user_id: int,
    current_user: CurrentUser = Depends(require_permissions("System:User:Delete")),
):
    """删除用户。"""

    user = await User.get_or_none(id=user_id).prefetch_related("roles")
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if user.username == current_user.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除当前登录用户")

    if await _is_super_user(user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="超级管理员不可删除")

    await user.delete()
    return ok(True)


@router.post("/{user_id}/reset-password", response_model=ApiResponse[bool])
async def reset_password(
    user_id: int,
    payload: SystemUserResetPassword,
    _current_user=Depends(require_permissions("System:User:ResetPassword")),
):
    """重置用户密码。"""

    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    _validate_password(payload.password)

    user.password_hash = get_password_hash(payload.password)
    await user.save()
    return ok(True)


@router.get("/options", response_model=ApiResponse[list[dict]])
async def list_user_options(
    keyword: str | None = Query(default=None),
    _current_user=Depends(require_permissions("System:User:List")),
):
    """获取用户选项（用于下拉选择）。"""

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

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import require_permissions
from app.core.config import settings
from app.models.menu import Menu
from app.models.role import Role
from app.schemas.response import ApiResponse, ok
from app.schemas.system_role import SystemRoleCreate, SystemRoleOut, SystemRoleUpdate

router = APIRouter()


def _format_dt(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


async def _get_all_menu_ids() -> list[int]:
    ids = await Menu.all().values_list("id", flat=True)
    return [int(i) for i in ids]


async def _role_permissions(role: Role) -> list[int]:
    if role.code == settings.SUPERUSER_ROLE_CODE:
        return await _get_all_menu_ids()
    ids = await role.menus.all().values_list("id", flat=True)
    return [int(i) for i in ids]


async def _set_role_permissions(role: Role, menu_ids: list[int]) -> None:
    await role.menus.clear()
    if not menu_ids:
        return
    menus = await Menu.filter(id__in=menu_ids).all()
    if menus:
        await role.menus.add(*menus)


@router.get("/list", response_model=ApiResponse[dict])
async def list_roles(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
    name: str | None = Query(default=None),
    id: str | None = Query(default=None),
    remark: str | None = Query(default=None),
    status_: str | None = Query(default=None, alias="status"),
    _user=Depends(require_permissions("System:Role:List")),
):
    """获取角色列表（分页）。"""

    qs = Role.all()
    if name:
        qs = qs.filter(name__icontains=name)
    if remark:
        qs = qs.filter(remark__icontains=remark)
    if id and str(id).isdigit():
        qs = qs.filter(id=int(id))
    if status_ in {"0", "1"}:
        qs = qs.filter(status=int(status_))

    total = await qs.count()
    roles = await qs.order_by("-id").offset((page - 1) * pageSize).limit(pageSize)

    items: list[SystemRoleOut] = []
    for role in roles:
        items.append(
            SystemRoleOut(
                id=role.id,
                name=role.name,
                status=role.status,
                remark=role.remark,
                permissions=await _role_permissions(role),
                createTime=_format_dt(role.created_at),
            ),
        )

    return ok({"items": items, "total": total})


@router.post("", response_model=ApiResponse[int])
async def create_role(payload: SystemRoleCreate, _user=Depends(require_permissions("System:Role:Create"))):
    """创建角色。"""

    role_code = f"role_{uuid4().hex[:8]}"
    role = await Role.create(
        name=payload.name,
        code=role_code,
        status=payload.status,
        remark=payload.remark,
    )
    await _set_role_permissions(role, payload.permissions)
    return ok(role.id)


@router.put("/{role_id}", response_model=ApiResponse[bool])
async def update_role(
    role_id: int,
    payload: SystemRoleUpdate,
    _user=Depends(require_permissions("System:Role:Edit")),
):
    """更新角色（支持部分字段）。"""

    role = await Role.get_or_none(id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    if role.code == settings.SUPERUSER_ROLE_CODE and payload.permissions is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="超级管理员权限不可修改",
        )

    data = payload.model_dump(exclude_unset=True)
    permissions = data.pop("permissions", None)

    for key, value in data.items():
        setattr(role, key, value)
    await role.save()

    if permissions is not None:
        await _set_role_permissions(role, permissions)

    return ok(True)


@router.delete("/{role_id}", response_model=ApiResponse[bool])
async def delete_role(role_id: int, _user=Depends(require_permissions("System:Role:Delete"))):
    """删除角色。"""

    role = await Role.get_or_none(id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    if role.code == settings.SUPERUSER_ROLE_CODE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="超级管理员角色不可删除",
        )

    if role.code == "user":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="默认用户角色不可删除")

    await role.delete()
    return ok(True)


@router.get("/options", response_model=ApiResponse[list[dict]])
async def list_role_options(_user=Depends(require_permissions("System:Role:List"))):
    """获取角色选项（用于下拉选择）。"""

    roles = await Role.all().order_by("id")
    return ok([{"id": r.id, "name": r.name, "code": r.code, "status": r.status} for r in roles])

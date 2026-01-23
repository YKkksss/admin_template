from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import require_permissions
from app.models.menu import Menu
from app.schemas.response import ApiResponse, ok
from app.schemas.system_menu import SystemMenuCreate, SystemMenuOut, SystemMenuUpdate
from app.services.menu import get_system_menu_tree

router = APIRouter()

_MENU_TYPES = {"catalog", "menu", "embedded", "link", "button"}


def _normalize_menu_payload(payload: SystemMenuCreate | SystemMenuUpdate) -> dict:
    data = payload.model_dump(exclude_unset=True)
    if "meta" in data and data["meta"] is None:
        data["meta"] = {}
    return data


@router.get("/list", response_model=ApiResponse[list[SystemMenuOut]])
async def list_menus(_user=Depends(require_permissions("System:Menu:List"))):
    """获取菜单树（用于菜单管理与角色授权）。"""

    data = await get_system_menu_tree()
    return ok(data)  # type: ignore[arg-type]


@router.get("/name-exists", response_model=ApiResponse[bool])
async def is_menu_name_exists(
    name: str = Query(default=""),
    id: int | None = Query(default=None),
    _user=Depends(require_permissions("System:Menu:List")),
):
    if not name or not name.strip():
        return ok(False)
    qs = Menu.filter(name=name)
    if id is not None:
        qs = qs.exclude(id=id)
    return ok(await qs.exists())


@router.get("/path-exists", response_model=ApiResponse[bool])
async def is_menu_path_exists(
    path: str = Query(default=""),
    id: int | None = Query(default=None),
    _user=Depends(require_permissions("System:Menu:List")),
):
    if not path or not path.strip():
        return ok(False)
    qs = Menu.filter(path=path)
    if id is not None:
        qs = qs.exclude(id=id)
    return ok(await qs.exists())


@router.post("", response_model=ApiResponse[int])
async def create_menu(payload: SystemMenuCreate, _user=Depends(require_permissions("System:Menu:Create"))):
    """创建菜单。"""

    data = _normalize_menu_payload(payload)
    menu_type = data.get("type", "menu")
    if menu_type not in _MENU_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="菜单类型不合法")

    # 唯一性校验
    if await Menu.filter(name=data["name"]).exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="菜单名称已存在")

    menu_path = data.get("path")
    if menu_path and await Menu.filter(path=menu_path).exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="菜单路径已存在")

    pid = data.pop("pid", None)
    parent = None
    if pid:
        parent = await Menu.get_or_none(id=pid)
        if not parent:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="父级菜单不存在")

    # 字段映射（camelCase -> snake_case）
    data["auth_code"] = data.pop("authCode", None)
    data["active_path"] = data.pop("activePath", None)

    # 规则补全
    if menu_type in {"embedded", "link"} and not data.get("component"):
        data["component"] = "IFrameView"
    if menu_type == "catalog":
        data["component"] = None
    if menu_type == "button":
        data["path"] = None
        data["component"] = None

    menu = await Menu.create(**data, parent=parent)
    return ok(menu.id)


@router.put("/{menu_id}", response_model=ApiResponse[bool])
async def update_menu(
    menu_id: int,
    payload: SystemMenuUpdate,
    _user=Depends(require_permissions("System:Menu:Edit")),
):
    """更新菜单。"""

    menu = await Menu.get_or_none(id=menu_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="菜单不存在")

    data = _normalize_menu_payload(payload)
    if "type" in data and data["type"] not in _MENU_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="菜单类型不合法")

    # 唯一性校验
    if "name" in data and await Menu.filter(name=data["name"]).exclude(id=menu_id).exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="菜单名称已存在")

    if "path" in data and data["path"]:
        if await Menu.filter(path=data["path"]).exclude(id=menu_id).exists():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="菜单路径已存在")

    pid = data.pop("pid", None)
    if "pid" in payload.model_fields_set:
        if pid:
            parent = await Menu.get_or_none(id=pid)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="父级菜单不存在",
                )
            if parent.id == menu_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="父级菜单不能是自己",
                )
            menu.parent = parent
        else:
            menu.parent = None

    # 字段映射
    if "authCode" in data:
        menu.auth_code = data.pop("authCode")
    if "activePath" in data:
        menu.active_path = data.pop("activePath")

    for key, value in data.items():
        setattr(menu, key, value)

    # 规则补全
    menu_type = menu.type
    if menu_type in {"embedded", "link"} and not menu.component:
        menu.component = "IFrameView"
    if menu_type == "catalog":
        menu.component = None
    if menu_type == "button":
        menu.path = None
        menu.component = None

    await menu.save()
    return ok(True)


@router.delete("/{menu_id}", response_model=ApiResponse[bool])
async def delete_menu(menu_id: int, _user=Depends(require_permissions("System:Menu:Delete"))):
    """删除菜单（级联删除子级）。"""

    menu = await Menu.get_or_none(id=menu_id)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="菜单不存在")

    await menu.delete()
    return ok(True)

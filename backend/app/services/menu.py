"""菜单与权限数据服务。

说明：
- sys_menu 用于承载“动态路由菜单”与“按钮权限点”两类数据。
- sys_role_menu 用于维护 角色 -> 菜单/按钮 的授权关系。
- 前端动态路由（@vben/access）需要的是 RouteRecordStringComponent 结构，
  因此这里会把 Menu 模型转换为路由记录结构并过滤掉 button 类型节点。
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Any

from app.core.config import settings
from app.models.menu import Menu
from app.models.user import User


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:  # noqa: BLE001 - 容错处理
        return default


def _get_order(meta: dict[str, Any] | None) -> int:
    if not isinstance(meta, dict):
        return 0
    return _as_int(meta.get("order", 0), 0)


def _sort_key(menu: Menu) -> tuple[int, int]:
    return (_get_order(menu.meta), menu.id)


def _build_tree(
    menus: Iterable[Menu],
    *,
    include_ids: set[int] | None = None,
    serializer: Callable[[Menu, list[dict] | None], dict],
) -> list[dict]:
    """
    将菜单列表构建为树形结构并序列化为 dict。

    参数：
    - include_ids：仅包含指定 id 的节点（及其已包含的子节点），为 None 则包含全部。
    - serializer：序列化函数，签名为 (menu: Menu, children: list[dict] | None) -> dict。
    """

    nodes = [m for m in menus if include_ids is None or m.id in include_ids]

    children_by_parent: dict[int | None, list[Menu]] = defaultdict(list)
    for node in nodes:
        children_by_parent[node.parent_id].append(node)

    for _, items in children_by_parent.items():
        items.sort(key=_sort_key)

    def build(parent_id: int | None) -> list[dict]:
        result: list[dict] = []
        for node in children_by_parent.get(parent_id, []):
            children = build(node.id)
            result.append(serializer(node, children if children else None))
        return result

    return build(None)


def _serialize_system_menu(menu: Menu, children: list[dict] | None) -> dict:
    payload: dict[str, Any] = {
        "id": menu.id,
        "pid": menu.parent_id,
        "name": menu.name,
        "type": menu.type,
        "path": menu.path,
        "component": menu.component,
        "activePath": menu.active_path,
        "authCode": menu.auth_code,
        "status": menu.status,
        "meta": menu.meta or {},
    }
    if children:
        payload["children"] = children
    return payload


def _serialize_route_menu(menu: Menu, children: list[dict] | None) -> dict:
    meta = dict(menu.meta or {})
    if menu.active_path:
        meta["activePath"] = menu.active_path

    payload: dict[str, Any] = {
        "name": menu.name,
        "path": menu.path,
    }

    if menu.component:
        payload["component"] = menu.component
    if meta:
        payload["meta"] = meta
    if children:
        payload["children"] = children

    return payload


async def get_system_menu_tree() -> list[dict]:
    """用于“菜单管理/角色授权”的完整菜单树（包含 button 节点）。"""

    menus = await Menu.all()
    return _build_tree(menus, serializer=_serialize_system_menu)


async def get_access_codes_for_roles(role_codes: list[str]) -> list[str]:
    """根据角色编码返回权限码集合（按钮/菜单 authCode）。"""

    if settings.SUPERUSER_ROLE_CODE in role_codes:
        codes = (
            await Menu.exclude(auth_code=None).values_list("auth_code", flat=True)  # type: ignore[arg-type]
        )
        return sorted({str(code) for code in codes if code})

    codes = (
        await Menu.filter(roles__code__in=role_codes)
        .exclude(auth_code=None)
        .values_list("auth_code", flat=True)  # type: ignore[arg-type]
    )
    return sorted({str(code) for code in codes if code})


async def get_routes_for_user(username: str) -> list[dict]:
    """
    获取用户可访问的路由菜单（用于 /menu/all）。

    说明：
    - 过滤掉 button 类型节点；
    - 对于非超级管理员：按角色授权过滤菜单，并自动补全父级目录节点。
    """

    user = await User.get_or_none(username=username, is_active=True)
    if not user:
        return []

    roles = await user.roles.filter(status=1).all()
    role_codes = [r.code for r in roles]

    base_qs = Menu.filter(status=1).exclude(type="button")

    # 超级管理员拥有全部菜单
    if settings.SUPERUSER_ROLE_CODE in role_codes:
        menus = await base_qs.all()
        return _build_tree(menus, serializer=_serialize_route_menu)

    permitted_ids = await base_qs.filter(roles__code__in=role_codes).values_list("id", flat=True)
    permitted_id_set = {int(i) for i in permitted_ids}
    if not permitted_id_set:
        return []

    all_menus = await base_qs.all()
    menu_by_id = {m.id: m for m in all_menus}

    include_ids: set[int] = set(permitted_id_set)
    for mid in list(permitted_id_set):
        parent_id = menu_by_id.get(mid).parent_id if menu_by_id.get(mid) else None
        while parent_id:
            include_ids.add(parent_id)
            parent_id = menu_by_id.get(parent_id).parent_id if menu_by_id.get(parent_id) else None

    return _build_tree(all_menus, include_ids=include_ids, serializer=_serialize_route_menu)

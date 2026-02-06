"""数据权限（数据范围）服务。

目标：
- 让“角色数据范围”落到各业务查询接口，统一计算并输出可复用的过滤条件。

说明：
- 数据范围是 RBAC 的补充：RBAC 解决“能不能看/能不能操作”，数据范围解决“能看多少数据”。
- 超级管理员默认不受数据范围限制（全放行）。
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from tortoise.expressions import Q

from app.core.config import settings
from app.models.dept import Dept
from app.models.role import DataScope, Role
from app.models.user import User
from app.schemas.user import CurrentUser


@dataclass(frozen=True)
class DataScopeResult:
    """数据范围计算结果。"""

    allow_all: bool
    allow_self: bool
    user_id: int | None
    dept_id: int | None
    dept_ids: set[int]


async def _build_dept_children_map() -> dict[int, list[int]]:
    """
    构建部门父子关系映射，用于递归获取子部门。

    返回：
    - key: parent_id（根节点使用 0）
    - value: children_ids
    """

    rows = await Dept.all().values("id", "parent_id")
    children: dict[int, list[int]] = {}
    for row in rows:
        did = int(row["id"])
        pid = int(row["parent_id"] or 0)
        children.setdefault(pid, []).append(did)
    return children


def _collect_dept_descendants(
    start_ids: Iterable[int],
    *,
    children_map: dict[int, list[int]],
) -> set[int]:
    """从给定部门集合出发，收集包含自身在内的所有子孙部门 ID。"""

    result: set[int] = set()
    stack = [int(i) for i in start_ids if int(i) > 0]

    while stack:
        current = stack.pop()
        if current in result:
            continue
        result.add(current)
        stack.extend(children_map.get(current, []))

    return result


async def get_data_scope_result(current_user: CurrentUser) -> DataScopeResult:
    """计算当前用户的数据范围。"""

    # 超级管理员全放行（不做数据范围限制）
    if settings.SUPERUSER_ROLE_CODE in current_user.roles:
        return DataScopeResult(
            allow_all=True,
            allow_self=False,
            user_id=None,
            dept_id=None,
            dept_ids=set(),
        )

    user = await User.get_or_none(username=current_user.username, is_active=True)
    if not user:
        # 理论上不该发生（token 解析成功但用户不存在/被禁用）
        return DataScopeResult(
            allow_all=False,
            allow_self=False,
            user_id=None,
            dept_id=None,
            dept_ids=set(),
        )

    roles = await Role.filter(code__in=current_user.roles, status=1).all()
    if not roles:
        # 没有任何启用角色时，按“仅本人”处理更安全
        return DataScopeResult(
            allow_all=False,
            allow_self=True,
            user_id=int(user.id),
            dept_id=int(user.dept_id) if user.dept_id else None,
            dept_ids=set(),
        )

    allow_all = False
    allow_self = False
    dept_ids: set[int] = set()

    # 仅在需要递归子部门时才构建映射，避免每次请求都扫描部门表
    need_children_map = any(
        r.data_scope in (DataScope.DEPT_AND_CHILDREN, DataScope.CUSTOM) for r in roles
    )
    children_map: dict[int, list[int]] = (
        await _build_dept_children_map() if need_children_map else {}
    )

    for role in roles:
        try:
            scope = DataScope(role.data_scope)
        except Exception:  # noqa: BLE001 - 兼容历史脏数据
            scope = DataScope.DEPT

        if scope == DataScope.ALL:
            allow_all = True
            break

        if scope == DataScope.SELF:
            allow_self = True
            continue

        if scope == DataScope.DEPT:
            if user.dept_id:
                dept_ids.add(int(user.dept_id))
            continue

        if scope == DataScope.DEPT_AND_CHILDREN:
            if user.dept_id:
                dept_ids |= _collect_dept_descendants(
                    [int(user.dept_id)],
                    children_map=children_map,
                )
            continue

        if scope == DataScope.CUSTOM:
            # 自定义部门默认包含其子部门（更符合“树选择”直觉）
            ids = await role.depts.all().values_list("id", flat=True)
            base_ids = {int(i) for i in ids}
            dept_ids |= _collect_dept_descendants(base_ids, children_map=children_map)
            continue

    return DataScopeResult(
        allow_all=allow_all,
        allow_self=allow_self,
        user_id=int(user.id),
        dept_id=int(user.dept_id) if user.dept_id else None,
        dept_ids=dept_ids,
    )


async def build_data_scope_q(
    current_user: CurrentUser,
    *,
    dept_field: str | None = None,
    user_field: str | None = None,
) -> Q | None:
    """
    构建可直接用于 Tortoise QuerySet.filter(...) 的 Q 条件。

    参数：
    - dept_field: 业务表中的部门字段名（如：dept_id、deptId、id 等）
    - user_field: 业务表中的“归属用户”字段名（如：creator_id、user_id、id 等）

    返回：
    - None：表示“全放行”（不需要额外 filter）
    - Q：可直接用于 .filter(q) 的条件
    """

    scope = await get_data_scope_result(current_user)
    if scope.allow_all:
        return None

    q: Q | None = None

    if dept_field and scope.dept_ids:
        dept_q = Q(**{f"{dept_field}__in": list(scope.dept_ids)})
        q = dept_q if q is None else (q | dept_q)

    if user_field and scope.allow_self and scope.user_id:
        user_q = Q(**{user_field: scope.user_id})
        q = user_q if q is None else (q | user_q)

    # 当既没有部门范围也没有本人范围时，返回“空集”条件，避免误放行
    return q if q is not None else Q(id=0)


async def get_allowed_user_ids(current_user: CurrentUser) -> set[int] | None:
    """
    将“部门范围/本人范围”转换为允许访问的用户 ID 集合。

    适用场景：
    - 业务表没有 dept_id，但有 user_id / creator_id 等归属字段；
    - 需要按部门范围控制“查看哪些人的数据”（如：在线会话、日志等）。

    返回：
    - None：全放行（不限制）
    - set：允许访问的 user_id 集合（可能为空）
    """

    scope = await get_data_scope_result(current_user)
    if scope.allow_all:
        return None

    allowed: set[int] = set()
    if scope.dept_ids:
        ids = await User.filter(dept_id__in=list(scope.dept_ids)).values_list("id", flat=True)
        allowed |= {int(i) for i in ids}

    if scope.allow_self and scope.user_id:
        allowed.add(int(scope.user_id))

    return allowed

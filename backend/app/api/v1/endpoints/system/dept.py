from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import require_permissions
from app.models.dept import Dept
from app.schemas.response import ApiResponse, ok
from app.schemas.system_dept import SystemDeptCreate, SystemDeptOut, SystemDeptUpdate

router = APIRouter()


def _format_dt(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def _node_from_dept(dept: Dept) -> dict:
    return {
        "id": dept.id,
        "pid": int(dept.parent_id or 0),
        "name": dept.name,
        "status": dept.status,
        "remark": dept.remark,
        "createTime": _format_dt(dept.created_at),
        "children": [],
    }


@router.get("/list", response_model=ApiResponse[list[SystemDeptOut]])
async def list_depts(_user=Depends(require_permissions("System:Dept:List"))):
    """获取部门树（用于部门管理与表单选择）。"""

    depts = await Dept.all().order_by("id")
    if not depts:
        return ok([])  # type: ignore[arg-type]

    nodes: dict[int, dict] = {}
    roots: list[dict] = []

    for dept in depts:
        nodes[dept.id] = _node_from_dept(dept)

    for dept in depts:
        node = nodes[dept.id]
        pid = int(dept.parent_id or 0)
        if pid and pid in nodes:
            nodes[pid]["children"].append(node)
        else:
            roots.append(node)

    return ok(roots)  # type: ignore[arg-type]


@router.post("", response_model=ApiResponse[int])
async def create_dept(payload: SystemDeptCreate, _user=Depends(require_permissions("System:Dept:Create"))):
    """创建部门。"""

    pid = payload.pid or 0
    parent = None
    if pid:
        parent = await Dept.get_or_none(id=pid)
        if not parent:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="上级部门不存在")

    dept = await Dept.create(
        name=payload.name,
        status=payload.status,
        remark=payload.remark,
        parent=parent,
    )
    return ok(dept.id)


@router.put("/{dept_id}", response_model=ApiResponse[bool])
async def update_dept(
    dept_id: int,
    payload: SystemDeptUpdate,
    _user=Depends(require_permissions("System:Dept:Edit")),
):
    """更新部门（支持部分字段）。"""

    dept = await Dept.get_or_none(id=dept_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")

    data = payload.model_dump(exclude_unset=True)
    pid = data.pop("pid", None)
    if "pid" in payload.model_fields_set:
        if pid:
            parent = await Dept.get_or_none(id=pid)
            if not parent:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="上级部门不存在")
            if parent.id == dept_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="上级部门不能是自己")
            dept.parent = parent
        else:
            dept.parent = None

    for key, value in data.items():
        setattr(dept, key, value)
    await dept.save()
    return ok(True)


@router.delete("/{dept_id}", response_model=ApiResponse[bool])
async def delete_dept(dept_id: int, _user=Depends(require_permissions("System:Dept:Delete"))):
    """删除部门。"""

    dept = await Dept.get_or_none(id=dept_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")

    if await Dept.filter(parent_id=dept_id).exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="存在下级部门，无法删除")

    await dept.delete()
    return ok(True)

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import require_permissions
from app.models.dict import DictData, DictType
from app.schemas.response import ApiResponse, ok
from app.schemas.system_dict import (
    DictDataCreate,
    DictDataOut,
    DictDataUpdate,
    DictOptionItem,
    DictTypeCreate,
    DictTypeOut,
    DictTypeUpdate,
)

router = APIRouter()


def _format_dt(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------
# 字典类型
# ---------------------------


@router.get("/type/list", response_model=ApiResponse[dict])
async def list_dict_types(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
    name: str | None = Query(default=None),
    code: str | None = Query(default=None),
    status_: int | None = Query(default=None, alias="status"),
    _current_user=Depends(require_permissions("System:DictType:List")),
):
    """获取字典类型列表（分页）。"""

    qs = DictType.all()
    if name:
        qs = qs.filter(name__icontains=name)
    if code:
        qs = qs.filter(code__icontains=code)
    if status_ in (0, 1):
        qs = qs.filter(status=status_)

    total = await qs.count()
    records = await qs.order_by("-id").offset((page - 1) * pageSize).limit(pageSize)

    items: list[DictTypeOut] = []
    for rec in records:
        items.append(
            DictTypeOut(
                id=rec.id,
                name=rec.name,
                code=rec.code,
                status=rec.status,
                remark=rec.remark,
                createTime=_format_dt(rec.created_at),
            ),
        )

    return ok({"items": items, "total": total})


# 兼容：部分前端/历史实现可能会请求 GET /type（不带 /list）
@router.get("/type", response_model=ApiResponse[dict])
async def list_dict_types_alias(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
    name: str | None = Query(default=None),
    code: str | None = Query(default=None),
    status_: int | None = Query(default=None, alias="status"),
    _current_user=Depends(require_permissions("System:DictType:List")),
):
    return await list_dict_types(page, pageSize, name, code, status_)  # type: ignore[misc]


@router.get("/type/options", response_model=ApiResponse[list[dict]])
async def list_dict_type_options(
    _current_user=Depends(require_permissions("System:DictType:List")),
):
    """获取字典类型选项（用于下拉选择）。"""

    records = await DictType.filter(status=1).order_by("id")
    return ok(
        [
            {
                "id": int(r.id),
                "name": r.name,
                "code": r.code,
                "status": int(r.status),
            }
            for r in records
        ],
    )


@router.post("/type", response_model=ApiResponse[int])
async def create_dict_type(
    payload: DictTypeCreate,
    _current_user=Depends(require_permissions("System:DictType:Create")),
):
    """创建字典类型。"""

    name = payload.name.strip()
    code = payload.code.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="字典名称不能为空")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="字典编码不能为空")

    if await DictType.filter(code=code).exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="字典编码已存在")

    rec = await DictType.create(
        name=name,
        code=code,
        status=payload.status,
        remark=payload.remark,
    )
    return ok(rec.id)


@router.put("/type/{type_id}", response_model=ApiResponse[bool])
async def update_dict_type(
    type_id: int,
    payload: DictTypeUpdate,
    _current_user=Depends(require_permissions("System:DictType:Edit")),
):
    """更新字典类型（不允许修改编码）。"""

    rec = await DictType.get_or_none(id=type_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="字典类型不存在")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        name = str(data["name"]).strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="字典名称不能为空")
        rec.name = name

    if "status" in data and data["status"] is not None:
        if data["status"] not in (0, 1):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="状态不合法")
        rec.status = int(data["status"])

    if "remark" in data:
        rec.remark = data.get("remark")

    await rec.save()
    return ok(True)


@router.delete("/type/{type_id}", response_model=ApiResponse[bool])
async def delete_dict_type(
    type_id: int,
    _current_user=Depends(require_permissions("System:DictType:Delete")),
):
    """删除字典类型（同时删除其下字典数据）。"""

    rec = await DictType.get_or_none(id=type_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="字典类型不存在")

    await DictData.filter(type_code=rec.code).delete()
    await rec.delete()
    return ok(True)


# ---------------------------
# 字典数据
# ---------------------------


@router.get("/data/list", response_model=ApiResponse[dict])
async def list_dict_data(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
    typeCode: str = Query(...),
    label: str | None = Query(default=None),
    value: str | None = Query(default=None),
    status_: int | None = Query(default=None, alias="status"),
    _current_user=Depends(require_permissions("System:DictData:List")),
):
    """获取字典数据列表（分页）。"""

    type_code = typeCode.strip()
    if not type_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="typeCode 不能为空")

    qs = DictData.filter(type_code=type_code)
    if label:
        qs = qs.filter(label__icontains=label)
    if value:
        qs = qs.filter(value__icontains=value)
    if status_ in (0, 1):
        qs = qs.filter(status=status_)

    total = await qs.count()
    records = (
        await qs.order_by("sort", "id").offset((page - 1) * pageSize).limit(pageSize)
    )

    items: list[DictDataOut] = []
    for rec in records:
        items.append(
            DictDataOut(
                id=rec.id,
                typeCode=rec.type_code,
                label=rec.label,
                value=rec.value,
                sort=rec.sort,
                status=rec.status,
                style=rec.style,
                remark=rec.remark,
                createTime=_format_dt(rec.created_at),
            ),
        )

    return ok({"items": items, "total": total})


# 兼容：部分前端/历史实现可能会请求 GET /data（不带 /list）
@router.get("/data", response_model=ApiResponse[dict])
async def list_dict_data_alias(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
    typeCode: str = Query(...),
    label: str | None = Query(default=None),
    value: str | None = Query(default=None),
    status_: int | None = Query(default=None, alias="status"),
    _current_user=Depends(require_permissions("System:DictData:List")),
):
    return await list_dict_data(  # type: ignore[misc]
        page,
        pageSize,
        typeCode,
        label,
        value,
        status_,
    )


@router.post("/data", response_model=ApiResponse[int])
async def create_dict_data(
    payload: DictDataCreate,
    _current_user=Depends(require_permissions("System:DictData:Create")),
):
    """创建字典数据。"""

    type_code = payload.typeCode.strip()
    if not type_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="字典类型编码不能为空")

    if not await DictType.filter(code=type_code).exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="字典类型不存在")

    if await DictData.filter(type_code=type_code, value=payload.value).exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该字典值已存在")

    rec = await DictData.create(
        type_code=type_code,
        label=payload.label,
        value=payload.value,
        sort=payload.sort,
        status=payload.status,
        style=payload.style,
        remark=payload.remark,
    )
    return ok(rec.id)


@router.put("/data/{data_id}", response_model=ApiResponse[bool])
async def update_dict_data(
    data_id: int,
    payload: DictDataUpdate,
    _current_user=Depends(require_permissions("System:DictData:Edit")),
):
    """更新字典数据（支持部分字段）。"""

    rec = await DictData.get_or_none(id=data_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="字典数据不存在")

    data = payload.model_dump(exclude_unset=True)

    next_type_code = rec.type_code
    next_value = rec.value

    if "typeCode" in data and data["typeCode"] is not None:
        type_code = str(data["typeCode"]).strip()
        if not type_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="字典类型编码不能为空",
            )
        if not await DictType.filter(code=type_code).exists():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="字典类型不存在")
        next_type_code = type_code

    if "value" in data and data["value"] is not None:
        next_value = str(data["value"])

    if next_type_code != rec.type_code or next_value != rec.value:
        exists = await DictData.filter(type_code=next_type_code, value=next_value).exclude(
            id=data_id,
        ).exists()
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该字典值已存在")

    rec.type_code = next_type_code
    rec.value = next_value

    if "label" in data and data["label"] is not None:
        rec.label = str(data["label"])

    if "sort" in data and data["sort"] is not None:
        rec.sort = int(data["sort"])

    if "status" in data and data["status"] is not None:
        if data["status"] not in (0, 1):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="状态不合法")
        rec.status = int(data["status"])

    if "style" in data:
        rec.style = data.get("style")
    if "remark" in data:
        rec.remark = data.get("remark")

    await rec.save()
    return ok(True)


@router.delete("/data/{data_id}", response_model=ApiResponse[bool])
async def delete_dict_data(
    data_id: int,
    _current_user=Depends(require_permissions("System:DictData:Delete")),
):
    """删除字典数据。"""

    rec = await DictData.get_or_none(id=data_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="字典数据不存在")

    await rec.delete()
    return ok(True)


@router.get("/data/options/{type_code}", response_model=ApiResponse[list[DictOptionItem]])
async def get_dict_options(
    type_code: str,
    _current_user=Depends(require_permissions("System:DictData:List")),
):
    """根据字典类型编码获取启用的字典项列表（用于下拉/单选）。"""

    code = type_code.strip()
    if not code:
        return ok([])

    records = await DictData.filter(type_code=code, status=1).order_by("sort", "id")
    return ok(
        [
            DictOptionItem(label=r.label, value=r.value, style=r.style)
            for r in records
        ],
    )

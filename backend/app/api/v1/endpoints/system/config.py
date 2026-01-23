from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import require_permissions
from app.models.config import Config
from app.schemas.response import ApiResponse, ok
from app.schemas.system_config import SystemConfigCreate, SystemConfigOut, SystemConfigUpdate

router = APIRouter()


def _format_dt(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


@router.get("/list", response_model=ApiResponse[dict])
async def list_configs(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
    configName: str | None = Query(default=None),
    configKey: str | None = Query(default=None),
    status_: int | None = Query(default=None, alias="status"),
    _current_user=Depends(require_permissions("System:Config:List")),
):
    """获取系统参数配置列表（分页）。"""

    qs = Config.all()
    if configName:
        qs = qs.filter(name__icontains=configName)
    if configKey:
        qs = qs.filter(key__icontains=configKey)
    if status_ in (0, 1):
        qs = qs.filter(status=status_)

    total = await qs.count()
    records = await qs.order_by("-id").offset((page - 1) * pageSize).limit(pageSize)

    items: list[SystemConfigOut] = []
    for cfg in records:
        items.append(
            SystemConfigOut(
                id=cfg.id,
                configName=cfg.name,
                configKey=cfg.key,
                configValue=cfg.value,
                status=cfg.status,
                remark=cfg.remark,
                isBuiltin=cfg.is_builtin,
                createTime=_format_dt(cfg.created_at),
            ),
        )

    return ok({"items": items, "total": total})


@router.post("", response_model=ApiResponse[int])
async def create_config(
    payload: SystemConfigCreate,
    _current_user=Depends(require_permissions("System:Config:Create")),
):
    """创建系统参数配置。"""

    name = payload.configName.strip()
    key = payload.configKey.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="配置名称不能为空")
    if not key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="配置键不能为空")

    if await Config.filter(key=key).exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="配置键已存在")

    cfg = await Config.create(
        name=name,
        key=key,
        value=payload.configValue,
        status=payload.status,
        remark=payload.remark,
        is_builtin=payload.isBuiltin,
    )
    return ok(cfg.id)


@router.put("/{config_id}", response_model=ApiResponse[bool])
async def update_config(
    config_id: int,
    payload: SystemConfigUpdate,
    _current_user=Depends(require_permissions("System:Config:Edit")),
):
    """更新系统参数配置（支持部分字段）。"""

    cfg = await Config.get_or_none(id=config_id)
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")

    data = payload.model_dump(exclude_unset=True)

    if "configKey" in data and data["configKey"] is not None:
        new_key = str(data["configKey"]).strip()
        if not new_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="配置键不能为空")
        if cfg.is_builtin and new_key != cfg.key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="内置配置不允许修改配置键",
            )
        if await Config.filter(key=new_key).exclude(id=config_id).exists():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="配置键已存在")
        cfg.key = new_key

    if "configName" in data and data["configName"] is not None:
        new_name = str(data["configName"]).strip()
        if not new_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="配置名称不能为空")
        cfg.name = new_name

    if "configValue" in data and data["configValue"] is not None:
        cfg.value = str(data["configValue"])

    if "status" in data and data["status"] is not None:
        if data["status"] not in (0, 1):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="状态不合法")
        cfg.status = int(data["status"])

    if "remark" in data:
        cfg.remark = data.get("remark")

    if "isBuiltin" in data and data["isBuiltin"] is not None:
        cfg.is_builtin = bool(data["isBuiltin"])

    await cfg.save()
    return ok(True)


@router.delete("/{config_id}", response_model=ApiResponse[bool])
async def delete_config(
    config_id: int,
    _current_user=Depends(require_permissions("System:Config:Delete")),
):
    """删除系统参数配置。"""

    cfg = await Config.get_or_none(id=config_id)
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")

    if cfg.is_builtin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="内置配置不允许删除")

    await cfg.delete()
    return ok(True)


@router.get("/by-key", response_model=ApiResponse[str | None])
async def get_config_value_by_key(
    configKey: str = Query(default=""),
    _current_user=Depends(require_permissions("System:Config:List")),
):
    """根据配置键获取配置值（未找到返回 null）。"""

    key = configKey.strip()
    if not key:
        return ok(None)

    cfg = await Config.get_or_none(key=key)
    return ok(cfg.value if cfg else None)

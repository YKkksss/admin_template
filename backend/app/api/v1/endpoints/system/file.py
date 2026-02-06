from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from starlette.responses import FileResponse

from app.api.v1.deps import require_permissions
from app.core.config import settings
from app.models.file import SysFile
from app.models.user import User
from app.schemas.monitor_log import IdsPayload
from app.schemas.response import ApiResponse, ok
from app.schemas.system_file import SystemFileOut
from app.schemas.user import CurrentUser
from app.services.data_scope import build_data_scope_q, get_data_scope_result

router = APIRouter()


def _format_dt(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def _ensure_storage_root() -> Path:
    root = settings.FILE_STORAGE_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root


def _get_ext(filename: str | None) -> str | None:
    if not filename:
        return None
    suffix = Path(filename).suffix
    if not suffix:
        return None
    ext = suffix.lstrip(".").lower()
    return ext or None


async def _save_upload_to_local(upload: UploadFile) -> tuple[str, int, str | None, str | None, str]:
    """
    保存上传文件到本地存储。

    返回：
    - object_key：相对路径（使用 / 分隔）
    - size：文件大小（字节）
    - sha256：哈希（可选）
    - mime：MIME 类型（可选）
    - stored_name：存储文件名
    """

    root = _ensure_storage_root()

    original_name = upload.filename or ""
    ext = _get_ext(original_name)
    stored_name = f"{uuid4().hex}{('.' + ext) if ext else ''}"
    subdir = datetime.now().strftime("%Y/%m/%d")
    object_key = f"{subdir}/{stored_name}"
    abs_path = root / Path(subdir) / stored_name
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    max_bytes = int(settings.FILE_MAX_SIZE_MB) * 1024 * 1024
    sha256 = hashlib.sha256()
    size = 0

    try:
        with abs_path.open("wb") as f:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if max_bytes > 0 and size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"文件过大，单文件最大 {settings.FILE_MAX_SIZE_MB}MB",
                    )
                sha256.update(chunk)
                f.write(chunk)
    except HTTPException:
        abs_path.unlink(missing_ok=True)
        raise
    except Exception as exc:  # noqa: BLE001 - 需要兜底返回友好错误
        abs_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存文件失败：{exc}",
        ) from exc
    finally:
        try:
            await upload.close()
        except Exception:
            pass

    return object_key, size, sha256.hexdigest(), upload.content_type, stored_name


async def _get_actor(current_user: CurrentUser) -> User:
    user = (
        await User.get_or_none(username=current_user.username, is_active=True)
        .prefetch_related("dept")
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    return user


async def _assert_can_access_file(rec: SysFile, current_user: CurrentUser) -> None:
    """校验当前用户是否可访问该文件（基于数据范围）。"""

    scope = await get_data_scope_result(current_user)
    if scope.allow_all:
        return

    # 满足任一条件即可访问：在部门范围内 或 仅本人且创建人是自己
    if rec.dept_id and int(rec.dept_id) in scope.dept_ids:
        return
    if (
        scope.allow_self
        and scope.user_id
        and rec.creator_id
        and int(rec.creator_id) == int(scope.user_id)
    ):
        return

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")


def _to_out(rec: SysFile) -> SystemFileOut:
    return SystemFileOut(
        id=int(rec.id),
        originalName=rec.original_name,
        fileName=rec.file_name,
        ext=rec.ext,
        mime=rec.mime,
        size=int(rec.size),
        storage=rec.storage,
        objectKey=rec.object_key,
        remark=rec.remark,
        creatorId=int(rec.creator_id) if rec.creator_id else None,
        creatorName=rec.creator_name,
        deptId=int(rec.dept_id) if rec.dept_id else None,
        deptName=rec.dept_name,
        createTime=_format_dt(rec.created_at),
    )


@router.get("/list", response_model=ApiResponse[dict])
async def list_files(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
    originalName: str | None = Query(default=None),
    creatorName: str | None = Query(default=None),
    deptId: int | None = Query(default=None),
    current_user: CurrentUser = Depends(require_permissions("System:File:List")),
):
    """文件列表（分页）。"""

    qs = SysFile.all()
    data_q = await build_data_scope_q(
        current_user,
        dept_field="dept_id",
        user_field="creator_id",
    )
    if data_q is not None:
        qs = qs.filter(data_q)

    if originalName and originalName.strip():
        qs = qs.filter(original_name__icontains=originalName.strip())
    if creatorName and creatorName.strip():
        qs = qs.filter(creator_name__icontains=creatorName.strip())
    if deptId:
        qs = qs.filter(dept_id=deptId)

    total = await qs.count()
    records = await qs.order_by("-id").offset((page - 1) * pageSize).limit(pageSize)
    items = [_to_out(r) for r in records]
    return ok({"items": items, "total": total})


@router.post("/upload", response_model=ApiResponse[SystemFileOut])
async def upload_file(
    file: UploadFile = File(..., description="上传文件"),
    remark: str | None = Form(default=None),
    current_user: CurrentUser = Depends(require_permissions("System:File:Upload")),
):
    """上传文件（本地存储）。"""

    actor = await _get_actor(current_user)

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件名不能为空")

    object_key, size, sha256, mime, stored_name = await _save_upload_to_local(file)

    rec = await SysFile.create(
        storage="local",
        original_name=file.filename,
        file_name=stored_name,
        ext=_get_ext(file.filename),
        mime=mime,
        size=size,
        sha256=sha256,
        object_key=object_key,
        remark=(remark.strip() if remark and remark.strip() else None),
        creator=actor,
        creator_name=actor.username,
        dept=actor.dept,
        dept_name=actor.dept.name if actor.dept else None,
    )

    return ok(_to_out(rec))


@router.get("/{file_id}/preview")
async def preview_file(
    file_id: int,
    current_user: CurrentUser = Depends(require_permissions("System:File:Download")),
):
    """预览文件（浏览器 inline）。"""

    rec = await SysFile.get_or_none(id=file_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    await _assert_can_access_file(rec, current_user)

    abs_path = _ensure_storage_root() / Path(rec.object_key)
    if not abs_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件已丢失")

    return FileResponse(
        path=str(abs_path),
        media_type=rec.mime or None,
        filename=rec.original_name,
        content_disposition_type="inline",
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: CurrentUser = Depends(require_permissions("System:File:Download")),
):
    """下载文件（浏览器 attachment）。"""

    rec = await SysFile.get_or_none(id=file_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    await _assert_can_access_file(rec, current_user)

    abs_path = _ensure_storage_root() / Path(rec.object_key)
    if not abs_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件已丢失")

    return FileResponse(
        path=str(abs_path),
        media_type=rec.mime or "application/octet-stream",
        filename=rec.original_name,
        content_disposition_type="attachment",
    )


@router.delete("/{file_id}", response_model=ApiResponse[bool])
async def delete_file(
    file_id: int,
    current_user: CurrentUser = Depends(require_permissions("System:File:Delete")),
):
    """删除文件（同时删除本地文件）。"""

    rec = await SysFile.get_or_none(id=file_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    await _assert_can_access_file(rec, current_user)

    abs_path = _ensure_storage_root() / Path(rec.object_key)
    try:
        abs_path.unlink(missing_ok=True)
    except Exception:
        # 删除失败不应阻塞数据库删除，避免出现“无法管理”的垃圾记录
        pass

    await rec.delete()
    return ok(True)


@router.post("/batch-delete", response_model=ApiResponse[int])
async def batch_delete_files(
    payload: IdsPayload,
    current_user: CurrentUser = Depends(require_permissions("System:File:Delete")),
):
    """批量删除文件（同时删除本地文件）。"""

    ids = [int(i) for i in (payload.ids or []) if int(i) > 0]
    if not ids:
        return ok(0)

    records = await SysFile.filter(id__in=ids).all()

    # 先做权限校验：只要存在一条无权限记录，就直接拒绝（避免“部分删除”带来的混乱）
    for rec in records:
        await _assert_can_access_file(rec, current_user)

    deleted = 0
    for rec in records:
        abs_path = _ensure_storage_root() / Path(rec.object_key)
        try:
            abs_path.unlink(missing_ok=True)
        except Exception:
            pass

        await rec.delete()
        deleted += 1

    return ok(deleted)

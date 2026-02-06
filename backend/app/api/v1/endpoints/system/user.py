from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from openpyxl import Workbook
from starlette.responses import StreamingResponse
from tortoise.expressions import Q

from app.api.v1.deps import require_permissions
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.dept import Dept
from app.models.role import Role
from app.models.user import User
from app.schemas.import_export import ImportErrorItem, ImportResult
from app.schemas.response import ApiResponse, ok
from app.schemas.system_user import (
    SystemUserCreate,
    SystemUserOut,
    SystemUserResetPassword,
    SystemUserUpdate,
)
from app.schemas.user import CurrentUser
from app.services.data_scope import build_data_scope_q
from app.utils.excel import ExcelColumn, append_sheet, export_xlsx_bytes, parse_xlsx_rows

router = APIRouter()

_XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _xlsx_response(content: bytes, filename: str) -> StreamingResponse:
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"}
    return StreamingResponse(BytesIO(content), media_type=_XLSX_MEDIA_TYPE, headers=headers)


def _user_export_columns() -> list[ExcelColumn]:
    return [
        ExcelColumn(title="用户名", key="username"),
        ExcelColumn(title="姓名", key="realName"),
        ExcelColumn(title="部门", key="deptName"),
        ExcelColumn(title="角色", key="roleNames"),
        ExcelColumn(title="状态", key="statusText"),
        ExcelColumn(title="创建时间", key="createTime"),
    ]


def _user_import_columns() -> list[ExcelColumn]:
    return [
        ExcelColumn(title="用户名", key="username", required=True),
        ExcelColumn(title="密码", key="password", required=True),
        ExcelColumn(title="姓名", key="realName", required=True),
        ExcelColumn(title="部门名称", key="deptName", required=False),
        ExcelColumn(title="角色编码", key="roleCodes", required=False),
        ExcelColumn(title="状态", key="status", required=False),
    ]


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
    current_user: CurrentUser = Depends(require_permissions("System:User:List")),
):
    """获取用户列表（分页）。"""

    qs = User.all()
    data_q = await build_data_scope_q(current_user, dept_field="dept_id", user_field="id")
    if data_q is not None:
        qs = qs.filter(data_q)
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


@router.get("/export")
async def export_users(
    username: str | None = Query(default=None),
    realName: str | None = Query(default=None),
    deptId: int | None = Query(default=None),
    status_: str | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(require_permissions("System:User:Export")),
):
    """导出用户列表（Excel）。"""

    qs = User.all()
    data_q = await build_data_scope_q(current_user, dept_field="dept_id", user_field="id")
    if data_q is not None:
        qs = qs.filter(data_q)

    if username and username.strip():
        qs = qs.filter(username__icontains=username.strip())
    if realName and realName.strip():
        qs = qs.filter(real_name__icontains=realName.strip())
    if deptId:
        qs = qs.filter(dept_id=deptId)
    if status_ in {"0", "1"}:
        qs = qs.filter(is_active=(status_ == "1"))

    total = await qs.count()
    if total > settings.EXCEL_EXPORT_MAX_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"导出数据量过大（{total}），最大允许 {settings.EXCEL_EXPORT_MAX_ROWS} 行",
        )

    users = await qs.order_by("-id").limit(settings.EXCEL_EXPORT_MAX_ROWS).prefetch_related(
        "roles",
        "dept",
    )

    rows: list[dict] = []
    for u in users:
        roles = list(u.roles) if hasattr(u, "roles") else []
        rows.append(
            {
                "username": u.username,
                "realName": u.real_name,
                "deptName": u.dept.name if u.dept else None,
                "roleNames": "、".join([str(r.name) for r in roles]),
                "statusText": "启用" if u.is_active else "禁用",
                "createTime": _format_dt(u.created_at),
            },
        )

    content = export_xlsx_bytes(sheet_name="用户列表", columns=_user_export_columns(), rows=rows)
    filename = f"用户列表_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    return _xlsx_response(content, filename)


@router.get("/import/template")
async def download_user_import_template(
    _current_user: CurrentUser = Depends(require_permissions("System:User:Import")),
):
    """下载用户导入模板（Excel）。"""

    wb = Workbook()
    # openpyxl 默认会创建一个 sheet，这里移除后按我们想要的顺序追加
    wb.remove(wb.active)

    append_sheet(
        wb,
        sheet_name="用户导入模板",
        columns=_user_import_columns(),
        rows=[],
    )

    roles = await Role.all().order_by("id")
    append_sheet(
        wb,
        sheet_name="角色参考",
        columns=[
            ExcelColumn(title="角色编码", key="code"),
            ExcelColumn(title="角色名称", key="name"),
            ExcelColumn(title="状态", key="statusText"),
        ],
        rows=[
            {
                "code": r.code,
                "name": r.name,
                "statusText": "启用" if r.status == 1 else "禁用",
            }
            for r in roles
        ],
    )

    depts = await Dept.all().prefetch_related("parent").order_by("id")
    append_sheet(
        wb,
        sheet_name="部门参考",
        columns=[
            ExcelColumn(title="部门名称", key="name"),
            ExcelColumn(title="上级部门", key="parentName"),
            ExcelColumn(title="状态", key="statusText"),
        ],
        rows=[
            {
                "name": d.name,
                "parentName": d.parent.name if d.parent else None,
                "statusText": "启用" if d.status == 1 else "禁用",
            }
            for d in depts
        ],
    )

    buf = BytesIO()
    wb.save(buf)
    return _xlsx_response(buf.getvalue(), "用户导入模板.xlsx")


@router.post("/import", response_model=ApiResponse[ImportResult])
async def import_users(
    file: UploadFile = File(..., description="xlsx 文件"),
    current_user: CurrentUser = Depends(require_permissions("System:User:Import")),
):
    """批量导入用户（Excel）。"""

    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 .xlsx 文件")

    content = await file.read()
    try:
        parsed_rows, parse_errors = parse_xlsx_rows(
            content=content,
            columns=_user_import_columns(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if len(parsed_rows) > settings.EXCEL_IMPORT_MAX_ROWS:
        max_rows = settings.EXCEL_IMPORT_MAX_ROWS
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"导入数据量过大（{len(parsed_rows)}），最大允许 {max_rows} 行",
        )

    result = ImportResult(total=len(parsed_rows))
    bad_rows = {e.row for e in parse_errors}
    for e in parse_errors:
        result.errors.append(ImportErrorItem(row=e.row, column=e.column, message=e.message))

    # 预加载角色与部门（减少循环内的数据库查询次数）
    roles = await Role.filter(status=1).all()
    role_by_code = {str(r.code).strip(): r for r in roles if r.code}

    depts = await Dept.filter(status=1).all()
    dept_by_name: dict[str, list[Dept]] = {}
    for d in depts:
        name = (d.name or "").strip()
        if not name:
            continue
        dept_by_name.setdefault(name, []).append(d)

    def parse_status(val: object | None) -> int:
        if val is None or val == "":
            return 1
        if isinstance(val, bool):
            return 1 if val else 0
        if isinstance(val, (int, float)):
            v = int(val)
            if v in {0, 1}:
                return v
            raise ValueError("状态只能是 0 或 1")
        s = str(val).strip()
        if s in {"0", "禁用", "停用", "否", "false", "False"}:
            return 0
        if s in {"1", "启用", "正常", "是", "true", "True"}:
            return 1
        raise ValueError("状态只能填写 0/1 或 启用/禁用")

    def parse_role_codes(val: object | None) -> list[str]:
        if val is None or val == "":
            return []
        s = str(val).strip()
        if not s:
            return []
        parts = [p.strip() for p in re.split(r"[,\n;，；、\s]+", s) if p and p.strip()]
        # 去重但保持顺序
        seen: set[str] = set()
        codes: list[str] = []
        for p in parts:
            if p in seen:
                continue
            seen.add(p)
            codes.append(p)
        return codes

    # 一次性查出本次导入中“已存在”的用户名，避免逐行 exists() 查询
    import_usernames: list[str] = []
    for row_idx, row in parsed_rows:
        if row_idx in bad_rows:
            continue
        u = row.get("username")
        if isinstance(u, str) and u.strip():
            import_usernames.append(u.strip())
    existing_usernames = set()
    if import_usernames:
        unique_usernames = list(set(import_usernames))
        existing_usernames = set(
            await User.filter(username__in=unique_usernames).values_list(
                "username",
                flat=True,
            ),
        )

    seen_in_file: set[str] = set()
    for row_idx, row in parsed_rows:
        if row_idx in bad_rows:
            result.failed += 1
            continue

        try:
            username = str(row.get("username") or "").strip()
            password = str(row.get("password") or "").strip()
            real_name = str(row.get("realName") or "").strip()
            dept_name = str(row.get("deptName") or "").strip()
            role_codes = parse_role_codes(row.get("roleCodes"))
            status_val = parse_status(row.get("status"))

            if not username:
                raise ValueError("用户名不能为空")
            if username in seen_in_file:
                raise ValueError("用户名在文件中重复")
            seen_in_file.add(username)
            if username in existing_usernames:
                raise ValueError("用户名已存在")
            if not real_name:
                raise ValueError("姓名不能为空")

            _validate_password(password)

            dept = None
            if dept_name:
                cands = dept_by_name.get(dept_name) or []
                if not cands:
                    raise ValueError(f"部门不存在：{dept_name}")
                if len(cands) > 1:
                    raise ValueError(f"部门名称不唯一，请使用更精确的部门：{dept_name}")
                dept = cands[0]

            role_ids: list[int] = []
            if role_codes:
                for code in role_codes:
                    role = role_by_code.get(code)
                    if not role:
                        raise ValueError(f"角色不存在或已禁用：{code}")
                    role_ids.append(int(role.id))

            user = await User.create(
                username=username,
                password_hash=get_password_hash(password),
                real_name=real_name,
                is_active=status_val == 1,
                dept=dept,
            )
            await _set_user_roles(user, role_ids, actor=current_user)

            result.success += 1
        except Exception as exc:  # noqa: BLE001 - 需要汇总错误并继续处理下一行
            result.failed += 1
            if isinstance(exc, HTTPException):
                msg = str(exc.detail)
            else:
                msg = str(exc)
            result.errors.append(ImportErrorItem(row=row_idx, column=None, message=msg))

    return ok(result)


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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="超级管理员角色不可修改",
        )

    if "status" in payload.model_fields_set and payload.status is not None:
        if is_super and payload.status == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="超级管理员不可禁用",
            )
        if user.username == current_user.username and payload.status == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能禁用当前登录用户",
            )

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
    current_user: CurrentUser = Depends(require_permissions("System:User:List")),
):
    """获取用户选项（用于下拉选择）。"""

    qs = User.filter(is_active=True)
    data_q = await build_data_scope_q(current_user, dept_field="dept_id", user_field="id")
    if data_q is not None:
        qs = qs.filter(data_q)
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

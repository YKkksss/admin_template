from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse

from app.api.v1.deps import get_current_user
from app.models.log import LoginLog
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.schemas.response import ApiResponse, ok
from app.schemas.user import CurrentUser
from app.services.auth import auth_service
from app.services.session import session_service
from app.utils.user_agent import parse_browser, parse_os

router = APIRouter()


@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(payload: LoginRequest, request: Request):
    """
    登录接口：
    - 返回 `accessToken` 给前端存储并用于后续请求的 Bearer Token。
    """

    username = payload.username.strip()
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    token = await auth_service.login(username, payload.password, ip=ip, user_agent=ua)
    if not token:
        try:
            await LoginLog.create(
                username=username or None,
                ip=ip,
                status=0,
                message="用户名或密码错误",
                browser=parse_browser(ua),
                os=parse_os(ua),
            )
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户名或密码错误")

    user = await User.get_or_none(username=username)
    try:
        await LoginLog.create(
            user_id=user.id if user else None,
            username=username,
            ip=ip,
            status=1,
            message="登录成功",
            browser=parse_browser(ua),
            os=parse_os(ua),
        )
    except Exception:
        pass

    return ok(LoginResponse(accessToken=token))


@router.post("/register", response_model=ApiResponse[RegisterResponse])
async def register(payload: RegisterRequest):
    """
    注册接口：
    - 创建新用户并分配默认角色（user）
    """

    username = payload.username.strip()
    password = payload.password

    if not username or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名和密码不能为空")

    if len(password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码长度至少 6 位")

    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码过长（bcrypt 最多 72 字节）",
        )

    user = await auth_service.register(username=username, password=password)
    if not user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")

    return ok(RegisterResponse(id=user.id, username=user.username))


@router.post("/logout", response_model=ApiResponse[str])
async def logout(current_user: CurrentUser = Depends(get_current_user)):
    """退出登录：撤销当前会话。"""

    try:
        await session_service.revoke_by_jti(
            username=current_user.username,
            jti=current_user.jti,
            revoked_by=current_user.username,
            reason="用户退出登录",
        )
    except Exception:
        # 退出登录不影响前端清理本地状态，失败时忽略即可
        pass
    return ok("")


@router.post("/refresh", response_class=PlainTextResponse)
async def refresh():
    """
    刷新 accessToken。

    重要说明：
    - 前端 refresh 调用使用的是 `baseRequestClient`（返回 AxiosResponse），并直接读取 `resp.data`，
      因此这里返回纯文本 token 字符串，保持与当前前端实现兼容。
    - 该接口后续可改造为基于 HttpOnly Cookie 的 refreshToken 机制。
    """

    token = auth_service.refresh_access_token()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新失败")
    return token


@router.get("/codes", response_model=ApiResponse[list[str]])
async def get_access_codes(current_user: CurrentUser = Depends(get_current_user)):
    """获取权限码（基础占位实现，后续会接入 RBAC 与数据库）。"""

    return ok(await auth_service.get_access_codes(current_user.roles))

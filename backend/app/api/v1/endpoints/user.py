from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import get_current_user
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.response import ApiResponse, ok
from app.schemas.user import CurrentUser, UserChangePassword, UserInfo, UserProfileUpdate
from app.services.auth import auth_service

router = APIRouter()


@router.get("/info", response_model=ApiResponse[UserInfo])
async def get_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """获取当前用户信息。"""

    user_info = await auth_service.get_user_info(current_user.username)
    if not user_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return ok(user_info)


@router.put("/profile", response_model=ApiResponse[UserInfo])
async def update_profile(
    payload: UserProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """更新当前用户基础信息（个人中心-基本设置）。"""

    user = await User.get_or_none(username=current_user.username, is_active=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    data = payload.model_dump(exclude_unset=True)

    if "realName" in data and data["realName"] is not None:
        user.real_name = data["realName"]

    if "avatar" in data:
        user.avatar = data.get("avatar")

    if "homePath" in data:
        user.home_path = data.get("homePath")

    if "introduction" in data:
        user.introduction = data.get("introduction")

    await user.save()

    # 复用统一的 userInfo 返回结构，保证前端刷新一致
    user_info = await auth_service.get_user_info(current_user.username)
    if not user_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return ok(user_info)


@router.post("/change-password", response_model=ApiResponse[bool])
async def change_password(
    payload: UserChangePassword,
    current_user: CurrentUser = Depends(get_current_user),
):
    """修改当前用户密码（个人中心-修改密码）。"""

    user = await User.get_or_none(username=current_user.username, is_active=True)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if not verify_password(payload.oldPassword, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码不正确")

    new_pwd = payload.newPassword
    if len(new_pwd.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码过长（bcrypt 最多 72 字节）",
        )

    # 新旧密码相同则提示
    if payload.oldPassword == new_pwd:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密码不能与旧密码相同")

    user.password_hash = get_password_hash(new_pwd)
    await user.save()

    return ok(True)

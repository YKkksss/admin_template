from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NoticeInboxItem(BaseModel):
    """收件箱列表项（用户维度）。"""

    id: int = Field(..., description="用户消息ID（sys_user_notice.id）")
    title: str = Field(..., description="标题")
    message: str = Field(..., description="摘要")
    type: int = Field(..., description="类型：1通知 2公告 3警告")
    link: str | None = Field(default=None, description="跳转链接")
    isRead: bool = Field(..., description="是否已读")
    createTime: str = Field(..., description="创建时间（格式化字符串）")
    readTime: str | None = Field(default=None, description="已读时间（格式化字符串）")


class NoticeDetail(BaseModel):
    """消息详情（用于抽屉展示）。"""

    id: int = Field(..., description="用户消息ID（sys_user_notice.id）")
    title: str = Field(..., description="标题")
    message: str = Field(..., description="摘要")
    content: str = Field(..., description="详情内容")
    type: int = Field(..., description="类型：1通知 2公告 3警告")
    link: str | None = Field(default=None, description="跳转链接")
    isRead: bool = Field(..., description="是否已读")
    createTime: str = Field(..., description="创建时间（格式化字符串）")
    readTime: str | None = Field(default=None, description="已读时间（格式化字符串）")


class NoticeOutboxItem(BaseModel):
    """发件箱列表项（消息内容维度）。"""

    id: int = Field(..., description="消息ID（sys_notice.id）")
    title: str = Field(..., description="标题")
    message: str = Field(..., description="摘要")
    type: int = Field(..., description="类型：1通知 2公告 3警告")
    link: str | None = Field(default=None, description="跳转链接")
    sendScope: str = Field(..., description="发送范围：all/dept/user/mixed/unknown")
    receiverCount: int = Field(..., description="接收人数")
    createTime: str = Field(..., description="创建时间（格式化字符串）")


class NoticeOutboxDetail(BaseModel):
    """发件箱详情（用于抽屉展示）。"""

    id: int = Field(..., description="消息ID（sys_notice.id）")
    title: str = Field(..., description="标题")
    message: str = Field(..., description="摘要")
    content: str = Field(..., description="详情内容")
    type: int = Field(..., description="类型：1通知 2公告 3警告")
    link: str | None = Field(default=None, description="跳转链接")

    sendAll: bool = Field(default=False, description="是否发送给全部用户")
    deptIds: list[int] = Field(default_factory=list, description="接收部门ID列表（可选）")
    userIds: list[int] = Field(default_factory=list, description="接收用户ID列表（可选）")
    deptNames: list[str] = Field(default_factory=list, description="接收部门名称列表（可选）")
    userNames: list[str] = Field(default_factory=list, description="接收用户展示名列表（可选）")

    sendScope: str = Field(..., description="发送范围：all/dept/user/mixed/unknown")
    receiverCount: int = Field(..., description="接收人数")
    createTime: str = Field(..., description="创建时间（格式化字符串）")


class NoticeSendRequest(BaseModel):
    """发送站内消息（管理员）。"""

    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field(..., min_length=1, description="详情内容")
    message: str | None = Field(
        default=None,
        max_length=500,
        description="摘要（可选，不填则自动截取）",
    )
    type: int = Field(default=1, ge=1, le=3, description="类型：1通知 2公告 3警告")
    link: str | None = Field(default=None, max_length=500, description="跳转链接（可选）")

    sendAll: bool = Field(default=False, description="是否发送给全部用户")
    deptIds: list[int] = Field(default_factory=list, description="接收部门ID列表（可选）")
    userIds: list[int] = Field(default_factory=list, description="接收用户ID列表")


class NoticeIdsRequest(BaseModel):
    """批量操作 ID 列表。"""

    ids: list[int] = Field(..., min_length=1, description="用户消息ID列表（sys_user_notice.id）")


class NoticeWsEvent(BaseModel):
    """WebSocket 推送事件（最小协议）。"""

    event: str = Field(..., description="事件类型，如 notice:new")
    timestamp: int = Field(..., description="服务端时间戳（秒）")
    data: dict = Field(default_factory=dict, description="事件数据（可选）")


def format_dt(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")

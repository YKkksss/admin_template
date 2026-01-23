from tortoise import fields

from app.models.base import BaseModel


class Notice(BaseModel):
    """站内通知/消息内容（可被多用户复用）。"""

    title = fields.CharField(max_length=200, description="消息标题")
    message = fields.CharField(max_length=500, description="消息摘要")
    content = fields.TextField(description="消息详情内容")
    type = fields.IntField(default=1, description="类型：1通知 2公告 3警告")
    link = fields.CharField(max_length=500, null=True, description="跳转链接（可选）")

    creator = fields.ForeignKeyField(
        "models.User",
        related_name="sent_notices",
        null=True,
        on_delete=fields.SET_NULL,
        description="发布人",
    )

    send_all = fields.BooleanField(default=False, description="是否发送给全部用户")
    dept_ids = fields.JSONField(null=True, description="发送部门ID列表（可选）")
    user_ids = fields.JSONField(null=True, description="发送用户ID列表（可选）")

    class Meta:
        table = "sys_notice"


class UserNotice(BaseModel):
    """用户收件箱（用户维度的已读/铃铛隐藏等状态）。"""

    user = fields.ForeignKeyField(
        "models.User",
        related_name="notices",
        on_delete=fields.CASCADE,
        description="接收用户",
    )
    notice = fields.ForeignKeyField(
        "models.Notice",
        related_name="receivers",
        on_delete=fields.CASCADE,
        description="消息内容",
    )

    is_read = fields.BooleanField(default=False, description="是否已读")
    read_at = fields.DatetimeField(null=True, description="已读时间")

    bell_hidden = fields.BooleanField(default=False, description="是否从铃铛列表隐藏")
    bell_hidden_at = fields.DatetimeField(null=True, description="铃铛隐藏时间")

    class Meta:
        table = "sys_user_notice"
        unique_together = (("user", "notice"),)

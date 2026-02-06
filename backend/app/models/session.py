from tortoise import fields

from app.models.base import BaseModel


class UserSession(BaseModel):
    """用户会话（用于在线用户与强制下线）。"""

    user = fields.ForeignKeyField(
        "models.User",
        related_name="sessions",
        on_delete=fields.CASCADE,
        description="用户",
    )
    username = fields.CharField(max_length=50, description="用户名（冗余字段，便于查询）")

    # JWT 标准字段：用于标识 Token 的唯一 ID
    jti = fields.CharField(max_length=64, unique=True, description="Token ID（JWT jti）")

    ip = fields.CharField(max_length=64, null=True, description="登录IP")
    user_agent = fields.CharField(max_length=512, null=True, description="User-Agent")
    browser = fields.CharField(max_length=100, null=True, description="浏览器信息")
    os = fields.CharField(max_length=100, null=True, description="操作系统")

    last_seen_at = fields.DatetimeField(null=True, description="最后活跃时间")
    expires_at = fields.DatetimeField(null=True, description="过期时间（来自 JWT exp）")

    status = fields.IntField(default=1, description="状态：1在线 0已下线/撤销")
    revoked_at = fields.DatetimeField(null=True, description="下线时间")
    revoke_reason = fields.CharField(max_length=255, null=True, description="下线原因")
    revoked_by = fields.CharField(max_length=50, null=True, description="操作人（用户名）")

    class Meta:
        table = "sys_user_session"
        indexes = [
            ("username", "status"),
            ("user_id", "status"),
        ]


"""审计日志相关模型。"""

from tortoise import fields
from tortoise.models import Model


class CreatedAtModel(Model):
    """仅包含创建时间的基础模型（适用于不可变的日志类表）。"""

    id = fields.IntField(pk=True, description="主键ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        abstract = True


class OperationLog(CreatedAtModel):
    """操作日志（审计日志）。"""

    user_id = fields.IntField(null=True, description="用户ID（可为空）")
    username = fields.CharField(max_length=50, null=True, description="用户名")
    module = fields.CharField(max_length=50, null=True, description="操作模块")
    action = fields.CharField(max_length=50, null=True, description="操作类型")
    method = fields.CharField(max_length=10, description="请求方法")
    url = fields.CharField(max_length=500, description="请求URL")
    ip = fields.CharField(max_length=50, null=True, description="IP地址")
    request_data = fields.TextField(null=True, description="请求数据（脱敏后）")
    response_data = fields.TextField(null=True, description="响应数据（摘要）")
    status = fields.IntField(null=True, description="状态：0失败 1成功")
    duration = fields.IntField(null=True, description="耗时(ms)")

    class Meta:
        table = "sys_operation_log"


class LoginLog(CreatedAtModel):
    """登录日志。"""

    user_id = fields.IntField(null=True, description="用户ID（可为空）")
    username = fields.CharField(max_length=50, null=True, description="用户名")
    ip = fields.CharField(max_length=50, null=True, description="IP地址")
    location = fields.CharField(max_length=100, null=True, description="登录地点（可选）")
    browser = fields.CharField(max_length=50, null=True, description="浏览器（可选）")
    os = fields.CharField(max_length=50, null=True, description="操作系统（可选）")
    status = fields.IntField(null=True, description="状态：0失败 1成功")
    message = fields.CharField(max_length=200, null=True, description="消息")

    class Meta:
        table = "sys_login_log"


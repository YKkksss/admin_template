from tortoise import fields

from app.models.base import BaseModel


class Config(BaseModel):
    """系统参数配置（用于运行期可调整的配置项）。"""

    name = fields.CharField(max_length=100, description="配置名称")
    key = fields.CharField(max_length=100, unique=True, description="配置键（唯一标识）")
    value = fields.TextField(description="配置值")
    status = fields.IntField(default=1, description="状态：1启用 0禁用")
    remark = fields.CharField(max_length=500, null=True, description="备注")
    is_builtin = fields.BooleanField(
        default=False,
        description="是否内置配置（内置配置不允许删除）",
    )

    class Meta:
        table = "sys_config"

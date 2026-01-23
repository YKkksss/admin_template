"""基础模型与公共字段。"""

from tortoise import fields
from tortoise.models import Model


class TimestampMixin(Model):
    """时间戳字段（创建时间、更新时间）。"""

    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        abstract = True


class BaseModel(TimestampMixin):
    """项目内的基础模型。"""

    id = fields.IntField(pk=True, description="主键ID")

    class Meta:
        abstract = True

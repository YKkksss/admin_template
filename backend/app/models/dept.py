from tortoise import fields

from app.models.base import BaseModel


class Dept(BaseModel):
    """部门模型（用于组织架构与权限管理扩展）。"""

    name = fields.CharField(max_length=50, description="部门名称")
    status = fields.IntField(default=1, description="状态：1启用 0禁用")
    remark = fields.CharField(max_length=50, null=True, description="备注")

    parent = fields.ForeignKeyField(
        "models.Dept",
        related_name="children",
        null=True,
        on_delete=fields.CASCADE,
        description="上级部门",
    )

    class Meta:
        table = "sys_dept"


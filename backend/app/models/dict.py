from tortoise import fields

from app.models.base import BaseModel


class DictType(BaseModel):
    """字典类型（字典分类）。"""

    name = fields.CharField(max_length=100, description="字典名称")
    code = fields.CharField(max_length=100, unique=True, description="字典编码（唯一标识）")
    status = fields.IntField(default=1, description="状态：1启用 0禁用")
    remark = fields.CharField(max_length=500, null=True, description="备注")

    class Meta:
        table = "sys_dict_type"


class DictData(BaseModel):
    """字典数据（字典项）。"""

    type_code = fields.CharField(max_length=100, index=True, description="字典类型编码")
    label = fields.CharField(max_length=100, description="字典标签（显示值）")
    value = fields.CharField(max_length=100, description="字典值（实际存储值）")
    sort = fields.IntField(default=0, description="排序")
    status = fields.IntField(default=1, description="状态：1启用 0禁用")
    style = fields.CharField(max_length=50, null=True, description="样式/颜色标记（可选）")
    remark = fields.CharField(max_length=500, null=True, description="备注")

    class Meta:
        table = "sys_dict_data"
        unique_together = (("type_code", "value"),)


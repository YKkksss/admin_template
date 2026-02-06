from enum import StrEnum

from tortoise import fields

from app.models.base import BaseModel


class DataScope(StrEnum):
    """角色数据范围枚举。"""

    ALL = "all"  # 全部数据权限
    CUSTOM = "custom"  # 自定义部门
    DEPT = "dept"  # 本部门
    DEPT_AND_CHILDREN = "dept_and_children"  # 本部门及子部门
    SELF = "self"  # 仅本人


class Role(BaseModel):
    """角色模型（RBAC）。"""

    name = fields.CharField(max_length=50, description="角色名称")
    code = fields.CharField(
        max_length=50,
        unique=True,
        description="角色编码（用于鉴权与 JWT roles）",
    )
    status = fields.IntField(default=1, description="状态：1启用 0禁用")
    remark = fields.CharField(max_length=255, null=True, description="备注")
    data_scope = fields.CharField(
        max_length=20,
        default=DataScope.DEPT,
        description="数据范围：all/custom/dept/dept_and_children/self",
    )

    depts = fields.ManyToManyField(
        "models.Dept",
        related_name="roles_data_scope",
        through="sys_role_dept",
        description="角色数据范围部门（data_scope=custom 时生效）",
    )

    menus = fields.ManyToManyField(
        "models.Menu",
        related_name="roles",
        through="sys_role_menu",
        description="角色菜单/权限关系",
    )

    class Meta:
        table = "sys_role"

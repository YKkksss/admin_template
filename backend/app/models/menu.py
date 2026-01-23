from tortoise import fields

from app.models.base import BaseModel


class Menu(BaseModel):
    """菜单模型（用于动态路由与权限点）。"""

    name = fields.CharField(
        max_length=50,
        unique=True,
        description="菜单名称（路由 name，需全局唯一）",
    )
    type = fields.CharField(
        max_length=20,
        default="menu",
        description="菜单类型：catalog/menu/embedded/link/button",
    )
    path = fields.CharField(
        max_length=255,
        null=True,
        unique=True,
        description="路由路径（按钮可为空）",
    )
    component = fields.CharField(
        max_length=255,
        null=True,
        description="前端组件标识（如 /system/menu/list 或 IFrameView）",
    )
    active_path = fields.CharField(
        max_length=255,
        null=True,
        description="激活菜单路径（用于高亮）",
    )
    auth_code = fields.CharField(
        max_length=100,
        null=True,
        unique=True,
        description="权限标识（菜单/按钮/接口权限码）",
    )
    meta = fields.JSONField(null=True, description="菜单元信息（图标、标题、排序等）")
    status = fields.IntField(default=1, description="状态：1启用 0禁用")

    parent = fields.ForeignKeyField(
        "models.Menu",
        related_name="children",
        null=True,
        on_delete=fields.CASCADE,
        description="父级菜单",
    )

    class Meta:
        table = "sys_menu"

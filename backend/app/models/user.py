from tortoise import fields

from app.models.base import BaseModel


class User(BaseModel):
    """用户模型。"""

    username = fields.CharField(max_length=50, unique=True, description="用户名")
    password_hash = fields.CharField(max_length=255, description="密码哈希")
    real_name = fields.CharField(max_length=50, description="真实姓名")
    introduction = fields.CharField(max_length=255, null=True, description="个人简介")
    avatar = fields.CharField(max_length=255, null=True, description="头像")
    home_path = fields.CharField(max_length=255, null=True, description="首页路径")
    is_active = fields.BooleanField(default=True, description="是否启用")

    dept = fields.ForeignKeyField(
        "models.Dept",
        related_name="users",
        null=True,
        on_delete=fields.SET_NULL,
        description="所属部门",
    )

    roles = fields.ManyToManyField(
        "models.Role",
        related_name="users",
        through="sys_user_role",
        description="用户角色关系",
    )

    class Meta:
        table = "sys_user"

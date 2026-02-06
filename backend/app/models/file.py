"""文件/附件相关模型。"""

from tortoise import fields

from app.models.base import BaseModel


class SysFile(BaseModel):
    """文件/附件（当前仅实现本地存储）。"""

    storage = fields.CharField(
        max_length=20,
        default="local",
        description="存储类型：local/minio/s3",
    )
    original_name = fields.CharField(max_length=255, description="原始文件名")
    file_name = fields.CharField(max_length=255, description="存储文件名")
    ext = fields.CharField(max_length=20, null=True, description="文件扩展名（不含 . ）")
    mime = fields.CharField(max_length=100, null=True, description="MIME 类型")
    size = fields.BigIntField(description="文件大小（字节）")
    sha256 = fields.CharField(max_length=64, null=True, description="SHA256（可选，用于去重/校验）")

    # 对象 key：本地存储时为相对于 FILE_STORAGE_ROOT 的路径（使用 / 分隔）
    object_key = fields.CharField(max_length=500, description="对象 key（本地为相对路径）")
    bucket = fields.CharField(max_length=100, null=True, description="Bucket（minio/s3 预留）")

    remark = fields.CharField(max_length=255, null=True, description="备注")

    creator = fields.ForeignKeyField(
        "models.User",
        related_name="files",
        null=True,
        on_delete=fields.SET_NULL,
        description="上传人",
    )
    creator_name = fields.CharField(max_length=50, null=True, description="上传人用户名（冗余）")

    dept = fields.ForeignKeyField(
        "models.Dept",
        related_name="files",
        null=True,
        on_delete=fields.SET_NULL,
        description="上传人所属部门",
    )
    dept_name = fields.CharField(max_length=50, null=True, description="上传人所属部门名称（冗余）")

    class Meta:
        table = "sys_file"
        indexes = [
            ("storage", "created_at"),
            ("creator_id", "created_at"),
            ("dept_id", "created_at"),
        ]


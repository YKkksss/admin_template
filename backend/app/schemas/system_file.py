"""系统文件/附件管理相关 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SystemFileOut(BaseModel):
    id: int = Field(..., description="文件ID")
    originalName: str = Field(..., description="原始文件名")
    fileName: str = Field(..., description="存储文件名")
    ext: str | None = Field(default=None, description="扩展名（不含 . ）")
    mime: str | None = Field(default=None, description="MIME 类型")
    size: int = Field(..., description="文件大小（字节）")
    storage: str = Field(default="local", description="存储类型：local/minio/s3")
    objectKey: str = Field(..., description="对象 key（本地为相对路径）")
    remark: str | None = Field(default=None, description="备注")
    creatorId: int | None = Field(default=None, description="上传人ID")
    creatorName: str | None = Field(default=None, description="上传人用户名")
    deptId: int | None = Field(default=None, description="部门ID")
    deptName: str | None = Field(default=None, description="部门名称")
    createTime: str | None = Field(default=None, description="上传时间")


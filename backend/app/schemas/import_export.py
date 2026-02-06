"""导入导出相关的通用 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ImportErrorItem(BaseModel):
    row: int = Field(..., description="Excel 行号（从 1 开始）")
    message: str = Field(..., description="错误信息")
    column: str | None = Field(default=None, description="列名（可选）")


class ImportResult(BaseModel):
    total: int = Field(default=0, description="总行数（不含表头）")
    success: int = Field(default=0, description="成功条数")
    failed: int = Field(default=0, description="失败条数")
    errors: list[ImportErrorItem] = Field(default_factory=list, description="失败明细（可选）")


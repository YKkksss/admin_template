"""数据字典 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DictTypeBase(BaseModel):
    name: str = Field(..., description="字典名称")
    code: str = Field(..., description="字典编码（唯一标识）")
    status: int = Field(default=1, description="状态：1启用 0禁用")
    remark: str | None = Field(default=None, description="备注")


class DictTypeCreate(DictTypeBase):
    pass


class DictTypeUpdate(BaseModel):
    name: str | None = Field(default=None, description="字典名称")
    status: int | None = Field(default=None, description="状态：1启用 0禁用")
    remark: str | None = Field(default=None, description="备注")


class DictTypeOut(DictTypeBase):
    id: int = Field(..., description="字典类型ID")
    createTime: str | None = Field(default=None, description="创建时间")


class DictDataBase(BaseModel):
    typeCode: str = Field(..., description="字典类型编码")
    label: str = Field(..., description="字典标签（显示值）")
    value: str = Field(..., description="字典值（实际存储值）")
    sort: int = Field(default=0, description="排序")
    status: int = Field(default=1, description="状态：1启用 0禁用")
    style: str | None = Field(default=None, description="样式/颜色标记（可选）")
    remark: str | None = Field(default=None, description="备注")


class DictDataCreate(DictDataBase):
    pass


class DictDataUpdate(BaseModel):
    typeCode: str | None = Field(default=None, description="字典类型编码")
    label: str | None = Field(default=None, description="字典标签（显示值）")
    value: str | None = Field(default=None, description="字典值（实际存储值）")
    sort: int | None = Field(default=None, description="排序")
    status: int | None = Field(default=None, description="状态：1启用 0禁用")
    style: str | None = Field(default=None, description="样式/颜色标记（可选）")
    remark: str | None = Field(default=None, description="备注")


class DictDataOut(DictDataBase):
    id: int = Field(..., description="字典数据ID")
    createTime: str | None = Field(default=None, description="创建时间")


class DictOptionItem(BaseModel):
    label: str = Field(..., description="显示标签")
    value: str = Field(..., description="实际值")
    style: str | None = Field(default=None, description="样式/颜色标记（可选）")


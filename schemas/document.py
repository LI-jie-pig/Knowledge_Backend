"""
文档模块 Pydantic 模型。
用于分类、列表、详情、上传等接口的请求/响应序列化。
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# 数据库 status 与前端字符串状态映射
STATUS_LABEL = {
    0: "pending",
    1: "parsing",
    2: "completed",
    3: "failed",
}


class DocumentCategoryResponse(BaseModel):
    """文档分类响应"""
    id: int
    name: str
    sort_order: int = Field(..., alias="sortOrder")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentResponse(BaseModel):
    """文档详情/上传成功响应（字段别名对齐前端 camelCase）"""
    id: int
    title: str
    description: str
    category_id: int = Field(..., alias="categoryId")
    category_name: Optional[str] = Field(None, alias="categoryName")
    file_name: str = Field(..., alias="fileName")
    file_size: int = Field(..., alias="fileSize")
    file_type: Optional[str] = Field(None, alias="fileType")
    status: str
    upload_time: datetime = Field(..., alias="uploadTime")
    preview_text: Optional[str] = Field(None, alias="previewText")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @classmethod
    def from_orm_doc(
        cls,
        doc,
        category_name: Optional[str] = None,
    ) -> "DocumentResponse":
        """从 ORM Document 对象构建响应，并把数字 status 转为前端字符串。"""
        return cls(
            id=doc.id,
            title=doc.title,
            description=doc.description,
            categoryId=doc.category_id,
            categoryName=category_name,
            fileName=doc.file_name,
            fileSize=doc.file_size,
            fileType=doc.file_type,
            status=STATUS_LABEL.get(doc.status, "pending"),
            uploadTime=doc.upload_time,
            previewText=doc.preview_text,
        )


class DocumentParseResponse(BaseModel):
    """文档解析结果 / 解析状态响应。"""
    id: int
    status: str
    preview_text: Optional[str] = Field(None, alias="previewText")
    chunk_count: int = Field(0, alias="chunkCount")
    parse_error: Optional[str] = Field(None, alias="parseError")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @classmethod
    def from_orm_doc(cls, doc) -> "DocumentParseResponse":
        """从 ORM Document 构建解析状态响应。"""
        return cls(
            id=doc.id,
            status=STATUS_LABEL.get(doc.status, "pending"),
            previewText=doc.preview_text,
            chunkCount=doc.chunk_count or 0,
            parseError=doc.parse_error,
        )

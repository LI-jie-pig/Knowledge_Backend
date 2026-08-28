from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models.documentCategory import DocumentCategory, Document


async def select_document_categories(
        db: AsyncSession
):
    result = await db.execute(select(DocumentCategory))
    return result.scalars().all()


async def get_category_by_id(
        db: AsyncSession,
        category_id: int,
):
    """按主键查询文档分类，不存在返回 None。"""
    result = await db.execute(
        select(DocumentCategory).where(DocumentCategory.id == category_id)
    )
    return result.scalar_one_or_none()


async def select_document(
        db: AsyncSession,
        page: int,
        page_size: int,
        category_id: int
):
    result = await db.execute(
        select(Document)
        .where(Document.category_id == category_id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    select_result = result.scalars().all()
    count = await db.execute(
        select(func.count(Document.id)).where(Document.category_id == category_id)
    )
    select_count = count.scalar_one_or_none()
    return select_result, select_count


async def query_detail_info(
    db: AsyncSession,
    document_id: int
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    return result.scalar_one_or_none()


async def create_document(
        db: AsyncSession,
        *,
        user_id: int,
        category_id: int,
        title: str,
        description: str,
        file_name: str,
        file_path: str,
        file_size: int,
        file_type: str | None,
        file_ext: str | None,
) -> Document:
    """
    创建文档记录。
    上传成功后 status=0（待解析），chunk_count=0。
    """
    category = await get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=400, detail="文档分类不存在")

    doc = Document(
        user_id=user_id,
        category_id=category_id,
        title=title,
        description=description,
        file_name=file_name,
        file_path=file_path,
        file_size=file_size,
        file_type=file_type,
        file_ext=file_ext,
        status=0,
        preview_text=None,
        parse_error=None,
        chunk_count=0,
        upload_time=datetime.now(),
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc

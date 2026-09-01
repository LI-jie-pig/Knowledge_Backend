from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from models.documentCategory import DocumentCategory, Document
from utils.minio_upload import PRESIGNED_EXPIRES_SECONDS, get_presigned_file_url


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


async def file_download_method(
        db: AsyncSession,
        document_id: int,
        disposition: str,
):
    """
    查询文档并生成 MinIO 预签名访问信息。
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        return None
    mode = "attachment" if disposition == "attachment" else "inline"
    url = get_presigned_file_url(
        file_path=doc.file_path,
        file_name=doc.file_name,
        file_type=doc.file_type,
        disposition=mode,
    )
    return {
        "url": url,
        "file_name": doc.file_name,
        "file_type": doc.file_type,
        "disposition": mode,
        "expires_in": PRESIGNED_EXPIRES_SECONDS,
    }


async def mark_document_parsing(
        db: AsyncSession,
        document_id: int,
) -> Document | None:
    """将文档标记为解析中（status=1），并清空上次错误信息。"""
    doc = await query_detail_info(db, document_id)
    if not doc:
        return None
    doc.status = 1
    doc.parse_error = None
    await db.flush()
    await db.refresh(doc)
    return doc


async def reset_document_for_reparse(
        db: AsyncSession,
        document_id: int,
) -> Document | None:
    """重新解析前重置预览与分片信息，并进入 parsing。"""
    doc = await query_detail_info(db, document_id)
    if not doc:
        return None
    doc.status = 1
    doc.preview_text = None
    doc.parse_error = None
    doc.chunk_count = 0
    await db.flush()
    await db.refresh(doc)
    return doc


async def save_parse_success(
        db: AsyncSession,
        document_id: int,
        *,
        preview_text: str,
        chunk_count: int,
) -> Document | None:
    """解析成功：写入预览文本与分片数，status=2。"""
    doc = await query_detail_info(db, document_id)
    if not doc:
        return None
    doc.status = 2
    doc.preview_text = preview_text
    doc.chunk_count = chunk_count
    doc.parse_error = None
    await db.flush()
    await db.refresh(doc)
    return doc


async def save_parse_failed(
        db: AsyncSession,
        document_id: int,
        parse_error: str,
) -> Document | None:
    """解析失败：写入错误原因，status=3。"""
    doc = await query_detail_info(db, document_id)
    if not doc:
        return None
    doc.status = 3
    doc.parse_error = parse_error
    await db.flush()
    await db.refresh(doc)
    return doc


async def delete_document(
        document_id: int,
        db: AsyncSession
):
    result = await db.execute(delete(Document).where(Document.id == document_id))
    await db.commit()
    return result.rowcount > 0
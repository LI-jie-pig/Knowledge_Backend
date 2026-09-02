import asyncio

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_database
from crud.document import (
    create_document,
    query_detail_info,
    select_document,
    select_document_categories,
    get_category_by_id,
    file_download_method, delete_document
)
from models.user import User
from schemas.document import DocumentParseResponse, DocumentResponse
from services.document_parse import parse_document
from utils.auth import get_user_by_token
from utils.minio_upload import upload_document_file
from utils.milvus_store import delete_document_vectors
from utils.response import success_response

router = APIRouter(prefix="/api/document", tags=["document"])


@router.get("/categories")
async def list_categories(
        db: AsyncSession = Depends(get_database)
):
    result = await select_document_categories(db)
    return success_response(data=result)


@router.get("/list")
async def list_document(
        db: AsyncSession = Depends(get_database),
        page: int = Query(1, alias="page"),
        page_size: int = Query(10, alias="pageSize"),
        category_id: int = Query(..., alias="categoryId")
):
    result_list, result_count = await select_document(db, page, page_size, category_id)
    return success_response(
        data={
            "list": result_list,
            "total": result_count,
            "hasMore": (page - 1) * page_size < result_count,
        },
        message="文档列表查询成功",
    )


@router.get("/detail")
async def query_detail(
    db: AsyncSession = Depends(get_database),
    document_id: int = Query(..., alias="id")
):
    result = await query_detail_info(db, document_id)
    if not result:
        raise HTTPException(status_code=404, detail="文档不存在")
    return success_response(data=result, message="查询成功")


@router.post("/upload")
async def upload_document(
        title: str = Form(..., min_length=1, max_length=100),
        description: str = Form(..., min_length=1, max_length=500),
        category_id: int = Form(..., alias="categoryId"),
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_database),
        user: User = Depends(get_user_by_token),
):
    """
    上传文档：文件写入 MinIO，元数据写入 document 表。
    表单字段：title / description / categoryId / file
    """
    title = title.strip()
    description = description.strip()
    # 标题、描述去空后再次校验
    if not title:
        raise HTTPException(status_code=400, detail="请填写文档标题")
    if not description:
        raise HTTPException(status_code=400, detail="请填写文档描述")
    if category_id <= 0:
        raise HTTPException(status_code=400, detail="请选择有效分类")

    category = await get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=400, detail="文档分类不存在")

    # 上传到 MinIO
    file_info = await upload_document_file(file)

    doc = await create_document(
        db,
        user_id=user.id,
        category_id=category_id,
        title=title,
        description=description,
        file_name=file_info["file_name"],
        file_path=file_info["file_path"],
        file_size=file_info["file_size"],
        file_type=file_info["file_type"],
        file_ext=file_info["file_ext"],
    )

    response_data = DocumentResponse.from_orm_doc(doc, category_name=category.name)
    return success_response(data=response_data, message="上传成功")


@router.get("/file")
async def file_download(
        db: AsyncSession = Depends(get_database),
        document_id: int = Query(..., alias="id"),
        disposition: str = Query("inline", alias="disposition"),
):
    if disposition not in ("inline", "attachment"):
        raise HTTPException(status_code=400, detail="disposition 仅支持 inline 或 attachment")

    result = await file_download_method(db, document_id, disposition)
    if not result:
        raise HTTPException(status_code=404, detail="文档不存在")

    return success_response(
        data={
            "url": result["url"],
            "fileName": result["file_name"],
            "fileType": result["file_type"],
            "disposition": result["disposition"],
            "expiresIn": result["expires_in"],
        },
        message="文档访问链接",
    )


@router.post("/parse")
async def parse_document_api(
        db: AsyncSession = Depends(get_database),
        document_id: int = Query(..., alias="id"),
        force: bool = Query(False, alias="force"),
        user: User = Depends(get_user_by_token),
):
    """
    同步解析文档：下载原文件 → 抽文本 → 分片 → 回写 preview/status/chunk_count。
    force=true 时允许对已完成文档重新解析。
    """
    _ = user
    doc = await parse_document(db, document_id, force=force)
    message = "解析完成" if doc.status == 2 else "解析失败"
    return success_response(
        data=DocumentParseResponse.from_orm_doc(doc),
        message=message,
    )


@router.get("/parse/status")
async def parse_status_api(
        db: AsyncSession = Depends(get_database),
        document_id: int = Query(..., alias="id"),
):
    """查询文档解析状态（供详情页轮询）。"""
    doc = await query_detail_info(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return success_response(
        data=DocumentParseResponse.from_orm_doc(doc),
        message="查询成功",
    )


@router.delete("/delete")
async def delete(
        db: AsyncSession = Depends(get_database),
        document_id: int = Query(..., alias="id"),
):
    # 先删 Milvus 分片向量，再删 MySQL 文档记录
    await asyncio.to_thread(delete_document_vectors, document_id)
    result = await delete_document(document_id, db)
    return success_response(data="", message="删除成功")

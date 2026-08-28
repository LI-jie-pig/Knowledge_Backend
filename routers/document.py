from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_database
from crud.document import (
    create_document,
    query_detail_info,
    select_document,
    select_document_categories,
    get_category_by_id,
)
from models.user import User
from schemas.document import DocumentResponse
from utils.auth import get_user_by_token
from utils.minio_upload import upload_document_file
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

"""
MinIO 文件上传工具。
负责将文档二进制写入对象存储，并返回可落库的路径信息。
"""
import io
import uuid
from datetime import datetime

from fastapi import HTTPException, UploadFile
from minio.error import S3Error

from config.minio_conf import (
    ALLOWED_EXTENSIONS,
    EXT_CONTENT_TYPE,
    MAX_FILE_SIZE,
    MINIO_BUCKET,
    MINIO_PUBLIC_BASE,
    ensure_bucket,
    minio_client,
)


def _extract_ext(filename: str) -> str:
    """从原始文件名解析扩展名（小写、不含点）。"""
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower().strip()


async def upload_document_file(file: UploadFile) -> dict:
    """
    校验并上传文档文件到 MinIO。

    返回:
        dict: file_name / file_path / file_size / file_type / file_ext
    """
    if file is None:
        raise HTTPException(status_code=400, detail="请选择要上传的文件")

    original_name = (file.filename or "").strip()
    if not original_name:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 扩展名白名单校验
    file_ext = _extract_ext(original_name)
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 pdf、txt、md 格式")

    content = await file.read()
    file_size = len(content)
    # 空文件与超大文件拦截
    if file_size <= 0:
        raise HTTPException(status_code=400, detail="上传文件不能为空")
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 50MB")

    content_type = (
        (file.content_type or "").strip()
        or EXT_CONTENT_TYPE.get(file_ext, "application/octet-stream")
    )

    # object key：按日期分目录，避免同名覆盖
    date_prefix = datetime.now().strftime("%Y/%m/%d")
    object_name = f"documents/{date_prefix}/{uuid.uuid4().hex}.{file_ext}"

    try:
        ensure_bucket()
        minio_client.put_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            data=io.BytesIO(content),
            length=file_size,
            content_type=content_type,
        )
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {e}") from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {
        "file_name": original_name,
        "file_path": f"{MINIO_PUBLIC_BASE}/{object_name}",
        "file_size": file_size,
        "file_type": content_type,
        "file_ext": file_ext,
    }

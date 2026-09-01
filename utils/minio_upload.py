"""
MinIO 文件上传与访问工具。
负责将文档二进制写入对象存储，并生成预签名访问链接。
"""
import io
import uuid
from datetime import datetime, timedelta
from urllib.parse import quote, urlparse

from fastapi import HTTPException, UploadFile
from minio.error import S3Error

from config.minio_conf import (
    ALLOWED_EXTENSIONS,
    EXT_CONTENT_TYPE,
    MAX_FILE_SIZE,
    MINIO_BUCKET,
    ensure_bucket,
    minio_client,
)

# 预签名链接默认有效期：1 小时
PRESIGNED_EXPIRES_SECONDS = 3600


def _extract_ext(filename: str) -> str:
    """从原始文件名解析扩展名（小写、不含点）。"""
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower().strip()


def resolve_object_key(file_path: str) -> str:
    """
    将库中 file_path 解析为 MinIO object key。
    兼容历史数据：完整 URL 或纯 object key 均可。
    """
    if not file_path:
        return ""
    path = file_path.strip()
    if path.startswith("http://") or path.startswith("https://"):
        parsed = urlparse(path)
        segments = parsed.path.lstrip("/").split("/", 1)
        if len(segments) == 2 and segments[0] == MINIO_BUCKET:
            return segments[1]
        return parsed.path.lstrip("/")
    return path.lstrip("/")


def _build_content_disposition(file_name: str, disposition: str) -> str:
    """构造 Content-Disposition，兼容中文文件名。"""
    mode = "attachment" if disposition == "attachment" else "inline"
    safe_name = file_name.replace('"', "")
    encoded = quote(safe_name)
    return f"{mode}; filename=\"{safe_name}\"; filename*=UTF-8''{encoded}"


def get_presigned_file_url(
    file_path: str,
    file_name: str,
    file_type: str | None = None,
    disposition: str = "inline",
    expires_seconds: int = PRESIGNED_EXPIRES_SECONDS,
) -> str:
    """
    根据 object key / 历史 URL 生成 MinIO 预签名访问链接。
    """
    object_key = resolve_object_key(file_path)
    if not object_key:
        raise HTTPException(status_code=404, detail="文件路径无效")

    mode = "attachment" if disposition == "attachment" else "inline"
    response_headers = {
        "response-content-disposition": _build_content_disposition(file_name, mode),
    }
    if file_type:
        response_headers["response-content-type"] = file_type

    try:
        return minio_client.presigned_get_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_key,
            expires=timedelta(seconds=expires_seconds),
            response_headers=response_headers,
        )
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"生成文件访问链接失败: {e}") from e


def download_object_bytes(file_path: str) -> bytes:
    """
    按 object key / 历史 URL 从 MinIO 下载文件二进制。
    供文档解析流水线使用。
    """
    object_key = resolve_object_key(file_path)
    if not object_key:
        raise HTTPException(status_code=404, detail="文件路径无效")

    response = None
    try:
        response = minio_client.get_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_key,
        )
        return response.read()
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {e}") from e
    finally:
        # 释放底层连接，避免连接泄漏
        if response is not None:
            response.close()
            response.release_conn()


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
        # 仅存 object key，访问时再生成预签名 URL
        # "file_path": f"{MINIO_PUBLIC_BASE}/{object_name}",
        "file_path": object_name,
        "file_size": file_size,
        "file_type": content_type,
        "file_ext": file_ext,
    }

"""
文档解析业务编排。
负责：校验状态 → 下载文件 → 抽文本 → 分片 → 回写 document 表。
"""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.parse_conf import PARSE_ERROR_MAX_LEN, PREVIEW_MAX_CHARS
from crud.document import (
    mark_document_parsing,
    query_detail_info,
    reset_document_for_reparse,
    save_parse_failed,
    save_parse_success,
)
from models.documentCategory import Document
from utils.chunking import split_text
from utils.minio_upload import download_object_bytes
from utils.parsers import get_parser


def _truncate_error(message: str) -> str:
    """截断错误信息，避免超出 parse_error 字段长度。"""
    text = (message or "解析失败").strip()
    if len(text) <= PARSE_ERROR_MAX_LEN:
        return text
    return text[: PARSE_ERROR_MAX_LEN - 3] + "..."


async def parse_document(
        db: AsyncSession,
        document_id: int,
        *,
        force: bool = False,
) -> Document:
    """
    同步解析指定文档。

    解析过程中的业务/系统错误会写入 status=failed 并返回文档，
    避免再抛异常导致会话回滚丢失失败状态。

    :param db: 数据库会话
    :param document_id: 文档 ID
    :param force: 是否强制重新解析（completed 也可重跑）
    :return: 更新后的 Document
    """
    # 文档必须存在
    doc = await query_detail_info(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 解析中不允许重复触发
    if doc.status == 1:
        raise HTTPException(status_code=409, detail="文档正在解析中，请稍后再试")

    # 已完成默认拒绝，需 force=true
    if doc.status == 2 and not force:
        raise HTTPException(
            status_code=400,
            detail="文档已解析完成，如需重新解析请传 force=true",
        )

    # pending / failed 直接进入 parsing；force 或失败重试时重置预览与分片
    if force or doc.status == 3:
        doc = await reset_document_for_reparse(db, document_id)
    else:
        doc = await mark_document_parsing(db, document_id)

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    try:
        file_bytes = download_object_bytes(doc.file_path)
        parser = get_parser(doc.file_ext)
        parse_result = parser.extract(file_bytes)
        full_text = (parse_result.text or "").strip()

        # 抽不出有效文本视为失败
        if not full_text:
            failed = await save_parse_failed(
                db,
                document_id,
                _truncate_error("未能从文件中提取到有效文本"),
            )
            return failed or doc

        chunks = split_text(full_text)
        preview = full_text[:PREVIEW_MAX_CHARS]
        success = await save_parse_success(
            db,
            document_id,
            preview_text=preview,
            chunk_count=len(chunks),
        )
        return success or doc
    except HTTPException as e:
        # 下载失败、格式不支持等：落库 failed，不再抛出以免回滚
        detail = e.detail if isinstance(e.detail, str) else str(e.detail)
        failed = await save_parse_failed(db, document_id, _truncate_error(detail))
        return failed or doc
    except Exception as e:
        failed = await save_parse_failed(
            db,
            document_id,
            _truncate_error(f"解析异常: {e}"),
        )
        return failed or doc

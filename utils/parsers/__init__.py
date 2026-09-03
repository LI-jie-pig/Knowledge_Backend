"""
文档解析器工厂。
按文件扩展名分发到对应解析器实现。
"""
from fastapi import HTTPException

from utils.parsers.base import BaseParser
from utils.parsers.image_parser import ImageParser
from utils.parsers.md_parser import MarkdownParser
from utils.parsers.pdf_parser import PdfParser
from utils.parsers.text_parser import TextParser

_PARSER_MAP: dict[str, type[BaseParser]] = {
    "pdf": PdfParser,
    "txt": TextParser,
    "md": MarkdownParser,
    "markdown": MarkdownParser,
    "png": ImageParser,
    "jpg": ImageParser,
    "jpeg": ImageParser,
    "webp": ImageParser,
    "gif": ImageParser,
}


def get_parser(file_ext: str | None) -> BaseParser:
    """
    根据扩展名返回解析器实例。

    :param file_ext: 文件扩展名（不含点）
    :return: BaseParser 实例
    """
    ext = (file_ext or "").strip().lower()
    parser_cls = _PARSER_MAP.get(ext)
    if not parser_cls:
        raise HTTPException(status_code=400, detail=f"暂不支持解析该格式: {ext or '未知'}")
    return parser_cls()

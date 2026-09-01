"""
PDF 解析器。
使用 pypdf 按页提取文本并拼接。
"""
import io

from pypdf import PdfReader

from utils.parsers.base import BaseParser, ParseResult


class PdfParser(BaseParser):
    """pdf 文件解析。"""

    def extract(self, content: bytes) -> ParseResult:
        if not content:
            return ParseResult(text="")

        reader = PdfReader(io.BytesIO(content))
        parts: list[str] = []
        for page in reader.pages:
            # 单页提取失败时跳过，避免整篇中断
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            if page_text.strip():
                parts.append(page_text.strip())

        return ParseResult(text="\n\n".join(parts))

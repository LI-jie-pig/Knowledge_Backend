"""
纯文本（txt）解析器。
尝试 utf-8 / gbk 解码，兼容常见中文编码。
"""
from utils.parsers.base import BaseParser, ParseResult


class TextParser(BaseParser):
    """txt 文件解析。"""

    def extract(self, content: bytes) -> ParseResult:
        if not content:
            return ParseResult(text="")

        # 优先 utf-8，失败再试 gbk，最后用替换策略兜底
        for encoding in ("utf-8", "gbk", "gb2312"):
            try:
                return ParseResult(text=content.decode(encoding))
            except UnicodeDecodeError:
                continue

        return ParseResult(text=content.decode("utf-8", errors="replace"))

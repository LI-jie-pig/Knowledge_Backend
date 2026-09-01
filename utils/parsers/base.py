"""
文档解析器基类与结果结构。
各格式解析器统一返回纯文本，供分片与预览使用。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ParseResult:
    """单次解析结果。"""
    text: str


class BaseParser(ABC):
    """文档解析器抽象基类。"""

    @abstractmethod
    def extract(self, content: bytes) -> ParseResult:
        """
        从文件二进制提取纯文本。

        :param content: 文件原始字节
        :return: ParseResult
        """
        raise NotImplementedError

"""
图片解析器。
将 png/jpg/webp/gif 送入百炼视觉模型抽取文字与结构。
"""
from utils.parsers.base import BaseParser, ParseResult
from utils.vision import describe_image_bytes


class ImageParser(BaseParser):
    """常见图片格式解析（依赖视觉模型）。"""

    def extract(self, content: bytes) -> ParseResult:
        if not content:
            return ParseResult(text="")

        text = describe_image_bytes(
            content,
            prompt=(
                "请完整提取图片中的全部可读文字，并保留层级/列表结构。"
                "若是流程图、思维导图、海报或截图，按分支或区块整理为清晰中文要点。"
                "不要编造图中不存在的内容。"
            ),
        )
        return ParseResult(text=text or "")

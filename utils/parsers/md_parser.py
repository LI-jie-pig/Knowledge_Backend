"""
Markdown 解析器。
首版按纯文本读取，不做语法剥离，便于后续 RAG 保留结构信息。
"""
from utils.parsers.text_parser import TextParser


class MarkdownParser(TextParser):
    """md / markdown 文件解析（暂复用文本解码逻辑）。"""
    pass

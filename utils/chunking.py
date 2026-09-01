"""
文本分片工具。
按固定字符窗口切分，供 RAG 阶段统计 chunk_count 与后续向量入库。
"""
from config.parse_conf import CHUNK_OVERLAP, CHUNK_SIZE


def split_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """
    将文本按字符数切分为有重叠的片段。

    :param text: 原文
    :param chunk_size: 单片最大字符数
    :param chunk_overlap: 相邻片重叠字符数
    :return: 非空 chunk 列表
    """
    content = (text or "").strip()
    if not content:
        return []

    # 参数兜底，避免 overlap >= size 导致死循环
    if chunk_size <= 0:
        chunk_size = CHUNK_SIZE
    if chunk_overlap < 0:
        chunk_overlap = 0
    if chunk_overlap >= chunk_size:
        chunk_overlap = max(0, chunk_size // 5)

    chunks: list[str] = []
    start = 0
    length = len(content)
    step = chunk_size - chunk_overlap

    while start < length:
        end = min(start + chunk_size, length)
        piece = content[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start += step

    return chunks

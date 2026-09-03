"""
PDF 解析器。
优先用 pypdf 抽文字层；单页文本过少时渲染为图并调用百炼视觉模型理解。
"""
import io

from pypdf import PdfReader

from config.vision_conf import PDF_RENDER_ZOOM, PDF_TEXT_MIN_CHARS
from utils.parsers.base import BaseParser, ParseResult
from utils.vision import describe_image_bytes


def _render_pdf_page_png(content: bytes, page_index: int, zoom: float) -> bytes:
    """
    将 PDF 指定页渲染为 PNG 字节。

    :param content: PDF 原始字节
    :param page_index: 页码（从 0 起）
    :param zoom: 渲染缩放
    :return: PNG bytes
    """
    import pymupdf

    doc = pymupdf.open(stream=content, filetype="pdf")
    try:
        if page_index < 0 or page_index >= doc.page_count:
            return b""
        page = doc.load_page(page_index)
        matrix = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()


class PdfParser(BaseParser):
    """pdf 文件解析（文本层 + 视觉理解兜底）。"""

    def extract(self, content: bytes) -> ParseResult:
        if not content:
            return ParseResult(text="")

        reader = PdfReader(io.BytesIO(content))
        parts: list[str] = []
        min_chars = PDF_TEXT_MIN_CHARS if PDF_TEXT_MIN_CHARS > 0 else 40

        for index, page in enumerate(reader.pages):
            # 单页提取失败时跳过文字层，改走视觉
            try:
                page_text = (page.extract_text() or "").strip()
            except Exception:
                page_text = ""

            # 文字层够用则直接采用；扫描件/纯图页走 VL
            if len(page_text) >= min_chars:
                print("page_text", len(page_text))
                parts.append(page_text)
                continue

            try:
                png_bytes = _render_pdf_page_png(content, index, PDF_RENDER_ZOOM)
            except Exception:
                png_bytes = b""

            if not png_bytes:
                if page_text:
                    parts.append(page_text)
                continue

            vision_text = describe_image_bytes(
                png_bytes,
                mime_type="image/png",
                prompt=(
                    f"这是一份 PDF 的第 {index + 1} 页。"
                    "请完整提取页内全部可读文字，并保留标题、列表、思维导图/流程图的层级结构。"
                    "用简洁中文整理；不要编造图中不存在的内容。"
                ),
            ).strip()

            # 视觉结果优先；若失败则退回已有少量文字
            if vision_text:
                parts.append(vision_text)
            elif page_text:
                parts.append(page_text)

        return ParseResult(text="\n\n".join(parts))

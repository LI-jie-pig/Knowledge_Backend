"""
百炼视觉理解（VL）配置。
用于扫描件 PDF / 图片类文档的图文内容抽取。
"""
import os

from config.embedding_conf import DASHSCOPE_API_BASE, DASHSCOPE_API_KEY

# 复用百炼 OpenAI 兼容地址与 Key
VISION_API_BASE = DASHSCOPE_API_BASE
VISION_API_KEY = DASHSCOPE_API_KEY

# 通义千问视觉模型（兼容 mode 已验证可用）
VISION_MODEL = os.getenv("VISION_MODEL", "qwen-vl-plus").strip()

# 单页生成上限
VISION_MAX_TOKENS = 2048

# PDF 单页文字少于此字符数时，改走视觉理解
PDF_TEXT_MIN_CHARS = 80

# 渲染 PDF 页为图片时的缩放（1.5~2.0 兼顾清晰度与体积）
PDF_RENDER_ZOOM = 1.8

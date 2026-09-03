"""
百炼视觉理解工具。
将图片（URL 或本地 bytes）送入 Qwen-VL，抽取可读文本与结构说明。
"""
import base64

from fastapi import HTTPException
from openai import OpenAI

from config.vision_conf import (
    VISION_API_BASE,
    VISION_API_KEY,
    VISION_MAX_TOKENS,
    VISION_MODEL,
)

_client: OpenAI | None = None

_DEFAULT_PROMPT = (
    "请完整提取图片中的全部可读文字，并保留层级/列表结构。"
    "若是流程图、思维导图、海报或截图，按分支或区块整理为清晰中文要点。"
    "不要编造图中不存在的内容；若几乎无文字，用一两句话概括画面主题即可。"
)


def _get_client() -> OpenAI:
    """获取百炼 OpenAI 兼容客户端。"""
    global _client
    if _client is None:
        if not VISION_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="未配置 DASHSCOPE_API_KEY，无法调用视觉模型",
            )
        _client = OpenAI(api_key=VISION_API_KEY, base_url=VISION_API_BASE)
    return _client


def _guess_mime(image_bytes: bytes) -> str:
    """根据文件头猜测 MIME。"""
    if image_bytes.startswith(b"\x89PNG"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[:16]:
        return "image/webp"
    if image_bytes.startswith(b"GIF8"):
        return "image/gif"
    return "image/png"


def describe_image_bytes(
        image_bytes: bytes,
        *,
        prompt: str | None = None,
        mime_type: str | None = None,
) -> str:
    """
    调用百炼视觉模型理解单张图片，返回文本描述/OCR 结果。

    :param image_bytes: 图片二进制
    :param prompt: 可选自定义提示词
    :param mime_type: 可选 MIME，缺省按文件头推断
    :return: 模型输出的中文文本
    """
    if not image_bytes:
        return ""

    mime = (mime_type or _guess_mime(image_bytes)).strip() or "image/png"
    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"
    text_prompt = (prompt or _DEFAULT_PROMPT).strip()

    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {"type": "text", "text": text_prompt},
                    ],
                }
            ],
            max_tokens=VISION_MAX_TOKENS,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"百炼视觉模型调用失败: {e}") from e

    if not response.choices:
        return ""
    content = response.choices[0].message.content
    return str(content or "").strip()

"""
DeepSeek 大模型调用工具。
使用 OpenAI 兼容 Chat Completions，支持流式输出。
"""
from collections.abc import Iterator

from fastapi import HTTPException
from openai import OpenAI

from config.llm_conf import (
    DEEPSEEK_API_BASE,
    DEEPSEEK_API_KEY,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_THINKING_ENABLED,
)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """获取 DeepSeek OpenAI 兼容客户端。"""
    global _client
    if _client is None:
        if not DEEPSEEK_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="未配置 DEEPSEEK_API_KEY，请在环境变量或 config/llm_conf.py 中设置",
            )
        _client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_API_BASE,
        )
    return _client


def stream_chat(messages: list[dict]) -> Iterator[str]:
    """
    流式调用大模型，逐段产出 assistant 文本增量。

    :param messages: OpenAI 格式 messages（含 system / user / assistant）
    :yield: 文本 delta 片段
    """
    if not messages:
        return

    client = _get_client()
    thinking_type = "enabled" if LLM_THINKING_ENABLED else "disabled"

    try:
        stream = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            stream=True,
            extra_body={"thinking": {"type": thinking_type}},
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None) or ""
            if content:
                yield content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DeepSeek 调用失败: {e}") from e

"""
对话记忆：基于 Redis 按 session 保存最近多轮消息。
"""
from config.cache_conf import get_json_cache, set_cache
from config.rag_conf import (
    CHAT_MEMORY_KEY_PREFIX,
    CHAT_MEMORY_MAX_MESSAGES,
    CHAT_MEMORY_TTL,
)


def _memory_key(session_id: str) -> str:
    """构造会话记忆 Redis key。"""
    return f"{CHAT_MEMORY_KEY_PREFIX}{session_id}"


async def get_chat_history(session_id: str) -> list[dict]:
    """
    读取会话历史消息。

    :param session_id: 前端会话 ID
    :return: [{role, content}, ...]
    """
    sid = (session_id or "").strip()
    if not sid:
        return []

    data = await get_json_cache(_memory_key(sid))
    if not isinstance(data, list):
        return []

    history: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        # 仅保留合法的 user / assistant 文本消息
        if role not in ("user", "assistant"):
            continue
        text = str(content or "").strip()
        if not text:
            continue
        history.append({"role": role, "content": text})
    return history


async def append_chat_turn(session_id: str, question: str, answer: str) -> None:
    """
    追加一轮问答到会话记忆，并按上限截断。

    :param session_id: 前端会话 ID
    :param question: 用户问题
    :param answer: 助手回答
    """
    sid = (session_id or "").strip()
    q = (question or "").strip()
    a = (answer or "").strip()
    if not sid or not q:
        return

    history = await get_chat_history(sid)
    history.append({"role": "user", "content": q})
    if a:
        history.append({"role": "assistant", "content": a})

    # 超长时丢弃最早消息，保留最近若干条
    max_n = CHAT_MEMORY_MAX_MESSAGES if CHAT_MEMORY_MAX_MESSAGES > 0 else 12
    if len(history) > max_n:
        history = history[-max_n:]

    await set_cache(_memory_key(sid), history, expire=CHAT_MEMORY_TTL)


async def clear_chat_history(session_id: str) -> None:
    """清空指定会话记忆。"""
    sid = (session_id or "").strip()
    if not sid:
        return
    # 用空列表覆盖并设短 TTL，避免依赖 delete 封装
    await set_cache(_memory_key(sid), [], expire=1)

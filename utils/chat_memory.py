"""
对话记忆：按 session_id 持久化到 MySQL，保留最近多轮消息。
"""
from config.db_conf import AsyncSessionLocal
from config.rag_conf import CHAT_MEMORY_MAX_MESSAGES
from crud.chat_memory import (
    add_chat_messages,
    delete_chat_messages,
    list_chat_messages,
    trim_chat_messages,
)


async def get_chat_history(session_id: str) -> list[dict]:
    """
    读取会话历史消息。

    :param session_id: 前端会话 ID
    :return: [{role, content}, ...]
    """
    sid = (session_id or "").strip()
    if not sid:
        return []

    async with AsyncSessionLocal() as db:
        rows = await list_chat_messages(db, sid)
        history: list[dict] = []
        for row in rows:
            role = row.role
            text = str(row.content or "").strip()
            # 仅保留合法的 user / assistant 文本消息
            if role not in ("user", "assistant") or not text:
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

    messages = [{"role": "user", "content": q}]
    if a:
        messages.append({"role": "assistant", "content": a})

    max_n = CHAT_MEMORY_MAX_MESSAGES if CHAT_MEMORY_MAX_MESSAGES > 0 else 12
    async with AsyncSessionLocal() as db:
        try:
            await add_chat_messages(db, sid, messages)
            await trim_chat_messages(db, sid, max_messages=max_n)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def clear_chat_history(session_id: str) -> None:
    """清空指定会话记忆。"""
    sid = (session_id or "").strip()
    if not sid:
        return

    async with AsyncSessionLocal() as db:
        try:
            await delete_chat_messages(db, sid)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

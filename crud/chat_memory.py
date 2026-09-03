"""
AI 会话记忆 CRUD。
按 session_id 读写/清空 chat_message 表，并按上限裁剪历史。
"""
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.rag_conf import CHAT_MEMORY_MAX_MESSAGES
from models.chat_message import ChatMessage


async def list_chat_messages(
        db: AsyncSession,
        session_id: str,
        *,
        limit: int | None = None,
) -> list[ChatMessage]:
    """
    按时间正序读取会话消息。

    :param db: 数据库会话
    :param session_id: 会话 ID
    :param limit: 最多返回条数；None 时用配置上限
    :return: ChatMessage 列表（旧 → 新）
    """
    max_n = limit if limit is not None else CHAT_MEMORY_MAX_MESSAGES
    if max_n is None or max_n <= 0:
        max_n = 12

    # 先取最近 max_n 条（倒序），再反转为正序供 prompt 使用
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.desc())
        .limit(max_n)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    rows.reverse()
    return rows


async def add_chat_messages(
        db: AsyncSession,
        session_id: str,
        messages: list[dict],
) -> None:
    """
    批量追加消息。

    :param db: 数据库会话
    :param session_id: 会话 ID
    :param messages: [{role, content}, ...]
    """
    entities: list[ChatMessage] = []
    for item in messages:
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        # 仅持久化合法的 user / assistant 文本
        if role not in ("user", "assistant") or not content:
            continue
        entities.append(
            ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
            )
        )
    if not entities:
        return
    db.add_all(entities)
    await db.flush()


async def trim_chat_messages(
        db: AsyncSession,
        session_id: str,
        *,
        max_messages: int | None = None,
) -> None:
    """
    超出上限时删除最早的消息，只保留最近若干条。

    :param db: 数据库会话
    :param session_id: 会话 ID
    :param max_messages: 保留上限
    """
    max_n = max_messages if max_messages is not None else CHAT_MEMORY_MAX_MESSAGES
    if max_n is None or max_n <= 0:
        max_n = 12

    count_stmt = select(func.count(ChatMessage.id)).where(
        ChatMessage.session_id == session_id
    )
    total = int((await db.execute(count_stmt)).scalar_one() or 0)
    # 未超限则无需裁剪
    if total <= max_n:
        return

    overflow = total - max_n
    # 按 id 升序取出最早 overflow 条主键后删除
    oldest_stmt = (
        select(ChatMessage.id)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .limit(overflow)
    )
    oldest_ids = list((await db.execute(oldest_stmt)).scalars().all())
    if not oldest_ids:
        return
    await db.execute(delete(ChatMessage).where(ChatMessage.id.in_(oldest_ids)))


async def delete_chat_messages(db: AsyncSession, session_id: str) -> None:
    """
    清空指定会话的全部消息。

    :param db: 数据库会话
    :param session_id: 会话 ID
    """
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))

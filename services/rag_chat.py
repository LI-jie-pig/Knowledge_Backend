"""
RAG 问答业务编排。
流程：向量召回 → 拼装上下文 → 带记忆调用 DeepSeek 流式生成 → 回写会话记忆。
"""
import asyncio
import json
import threading
import uuid
from collections.abc import AsyncIterator

from config.rag_conf import RAG_CHUNK_MAX_CHARS, RAG_TOP_K
from utils.chat_memory import append_chat_turn, clear_chat_history, get_chat_history
from utils.llm import stream_chat
from utils.milvus_store import search_document_chunks

SYSTEM_PROMPT = """你是知识库问答助手。请严格依据「参考文档」回答用户问题。
规则：
1. 只根据参考文档中的信息作答；文档未覆盖的内容请明确说明「根据现有知识库无法确定」。
2. 回答简洁、准确，可用分点说明；不要编造文档中不存在的内容。
3. 若参考文档为空，直接告知知识库暂无相关内容，并建议用户换个问法或先上传/解析文档。
4. 使用中文回答。"""


def _clip_chunk(text: str) -> str:
    """截断过长分片，控制 prompt 体积。"""
    content = (text or "").strip()
    if len(content) <= RAG_CHUNK_MAX_CHARS:
        return content
    return content[: RAG_CHUNK_MAX_CHARS - 3] + "..."


def _build_context(chunks: list[dict]) -> str:
    """将召回分片格式化为可注入 prompt 的参考文档文本。"""
    if not chunks:
        return "（暂无相关文档分片）"

    parts: list[str] = []
    for index, item in enumerate(chunks, start=1):
        title = item.get("title") or item.get("file_name") or "未命名文档"
        body = _clip_chunk(str(item.get("content") or ""))
        parts.append(f"[{index}] 《{title}》\n{body}")
    return "\n\n".join(parts)


def _build_messages(
        question: str,
        chunks: list[dict],
        history: list[dict],
) -> list[dict]:
    """组装 system + 历史 + 当前带上下文的 user 消息。"""
    context = _build_context(chunks)
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 注入历史轮次（不含当前问题）
    for item in history:
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    user_prompt = (
        f"参考文档：\n{context}\n\n"
        f"用户问题：{question}\n\n"
        "请基于参考文档回答。"
    )
    messages.append({"role": "user", "content": user_prompt})
    return messages


def _sse(event: dict) -> str:
    """编码为 SSE data 行。"""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


async def _iter_llm_deltas(messages: list[dict]) -> AsyncIterator[str]:
    """
    在线程中消费同步 LLM 流，经队列异步产出 delta。
    避免阻塞 FastAPI 事件循环。
    """
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[str | BaseException | None] = asyncio.Queue()

    def _worker() -> None:
        try:
            for delta in stream_chat(messages):
                loop.call_soon_threadsafe(queue.put_nowait, delta)
            loop.call_soon_threadsafe(queue.put_nowait, None)
        except BaseException as exc:  # noqa: BLE001 - 需传到异步侧
            loop.call_soon_threadsafe(queue.put_nowait, exc)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            if isinstance(item, BaseException):
                raise item
            yield item
    finally:
        await asyncio.to_thread(thread.join)


async def stream_rag_chat(
        *,
        question: str,
        session_id: str | None = None,
        document_id: int | None = None,
        top_k: int = RAG_TOP_K,
) -> AsyncIterator[str]:
    """
    执行一次 RAG 流式问答，产出 SSE 文本帧。

    事件类型：
    - session: 会话 ID
    - sources: 召回分片摘要
    - delta: 回答增量
    - done: 结束
    - error: 错误
    """
    q = (question or "").strip()
    if not q:
        yield _sse({"type": "error", "message": "问题不能为空"})
        return

    sid = (session_id or "").strip() or uuid.uuid4().hex
    yield _sse({"type": "session", "sessionId": sid})

    try:
        # 1) 向量召回（同步 IO，放线程池）
        chunks = await asyncio.to_thread(
            search_document_chunks,
            q,
            top_k=top_k,
            document_id=document_id,
        )
        sources = [
            {
                "documentId": item["document_id"],
                "title": item["title"],
                "fileName": item["file_name"],
                "chunkIndex": item["chunk_index"],
                "score": item["score"],
                "snippet": _clip_chunk(item["content"])[:160],
            }
            for item in chunks
        ]
        yield _sse({"type": "sources", "sources": sources})

        # 2) 读取对话记忆并拼装 prompt
        history = await get_chat_history(sid)
        messages = _build_messages(q, chunks, history)

        # 3) 流式生成
        answer_parts: list[str] = []
        async for delta in _iter_llm_deltas(messages):
            answer_parts.append(delta)
            yield _sse({"type": "delta", "content": delta})

        answer = "".join(answer_parts).strip()
        if not answer:
            answer = "根据现有知识库未能生成有效回答，请换个问法或确认文档已完成解析。"
            yield _sse({"type": "delta", "content": answer})

        # 4) 回写记忆（存用户原问题 + 完整回答）
        await append_chat_turn(sid, q, answer)
        yield _sse({"type": "done", "sessionId": sid})
    except Exception as e:
        detail = getattr(e, "detail", None)
        message = detail if isinstance(detail, str) else str(e)
        yield _sse({"type": "error", "message": message or "问答失败"})


async def reset_chat_session(session_id: str) -> None:
    """清空指定会话的对话记忆。"""
    await clear_chat_history(session_id)

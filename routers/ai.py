"""
AI 问答路由。
提供基于文档知识库的流式 RAG 对话，以及清空会话记忆。
"""
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.rag_chat import reset_chat_session, stream_rag_chat
from utils.response import success_response

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatRequest(BaseModel):
    """流式问答请求体。"""

    question: str = Field(..., min_length=1, description="用户问题")
    session_id: str | None = Field(None, alias="sessionId", description="会话 ID，用于多轮记忆")
    document_id: int | None = Field(None, alias="documentId", description="可选，限定单文档检索")
    top_k: int | None = Field(None, alias="topK", description="召回条数，默认服务端配置")

    model_config = {"populate_by_name": True}


class ClearChatRequest(BaseModel):
    """清空会话请求体。"""

    session_id: str = Field(..., alias="sessionId", min_length=1)

    model_config = {"populate_by_name": True}


@router.post("/chat")
async def chat_api(body: ChatRequest):
    """
    文档召回 + DeepSeek 流式回答（SSE）。

    事件：session / sources / delta / done / error
    """
    question = (body.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")
    if len(question) > 2000:
        raise HTTPException(status_code=400, detail="问题过长，请精简后再问")

    session_id = (body.session_id or "").strip() or uuid.uuid4().hex
    document_id = body.document_id
    # 非法 documentId 直接忽略，走全库检索
    if document_id is not None and document_id <= 0:
        document_id = None

    top_k = body.top_k if body.top_k and body.top_k > 0 else None

    async def event_stream():
        kwargs = {
            "question": question,
            "session_id": session_id,
            "document_id": document_id,
        }
        if top_k is not None:
            kwargs["top_k"] = min(top_k, 20)
        async for chunk in stream_rag_chat(**kwargs):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/clear")
async def clear_chat_api(body: ClearChatRequest):
    """清空指定会话的对话记忆。"""
    session_id = (body.session_id or "").strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="sessionId 不能为空")
    await reset_chat_session(session_id)
    return success_response(data={"sessionId": session_id}, message="会话已清空")

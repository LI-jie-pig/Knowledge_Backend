"""
文本 Embedding 工具。
调用阿里云百炼 text-embedding-v4（OpenAI 兼容 /embeddings）生成向量。
"""
from fastapi import HTTPException
from openai import OpenAI

from config.embedding_conf import (
    DASHSCOPE_API_BASE,
    DASHSCOPE_API_KEY,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """获取百炼 OpenAI 兼容客户端。"""
    global _client
    if _client is None:
        # API Key 未配置时直接拦截，避免无意义远程请求
        if not DASHSCOPE_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="未配置 DASHSCOPE_API_KEY，请在环境变量或 config/embedding_conf.py 中设置",
            )
        _client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=DASHSCOPE_API_BASE,
        )
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    将文本列表转为 embedding 向量列表。

    :param texts: 待向量化的文本
    :return: 与 texts 等长的 float 向量列表
    """
    if not texts:
        return []

    client = _get_client()
    vectors: list[list[float]] = []
    batch_size = EMBEDDING_BATCH_SIZE if EMBEDDING_BATCH_SIZE > 0 else 10

    try:
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch,
                dimensions=EMBEDDING_DIM,
                encoding_format="float",
            )
            # 按 index 排序，保证与入参顺序一致
            ordered = sorted(response.data, key=lambda item: item.index)
            for item in ordered:
                vector = list(item.embedding)
                # 维度校验，防止与 Milvus schema 不一致
                if len(vector) != EMBEDDING_DIM:
                    raise HTTPException(
                        status_code=500,
                        detail=(
                            f"Embedding 维度不匹配：期望 {EMBEDDING_DIM}，实际 {len(vector)}。"
                            f"请同步修改 config/embedding_conf.py 与 config/milvus_conf.py"
                        ),
                    )
                vectors.append(vector)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"百炼 Embedding 调用失败: {e}") from e

    if len(vectors) != len(texts):
        raise HTTPException(status_code=500, detail="Embedding 返回数量与输入不一致")

    return vectors

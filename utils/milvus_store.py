"""
Milvus 文档分片向量存储。
解析完成后将 chunk 文本 + embedding 写入 Milvus；删除/重解析时按 document_id 清理。
"""
from pymilvus import DataType, MilvusClient

from config.milvus_conf import (
    EMBEDDING_DIM,
    MILVUS_COLLECTION,
    MILVUS_CONTENT_MAX_LEN,
    MILVUS_METRIC_TYPE,
    MILVUS_URI,
)
from config.rag_conf import RAG_SCORE_THRESHOLD, RAG_TOP_K
from utils.embedding import embed_texts

_client: MilvusClient | None = None


def _get_client() -> MilvusClient:
    """获取 Milvus 客户端单例。"""
    # 使用 global, 表明要修改模块级的 _client 变量，这里的_client类似java的静态变量
    global _client
    if _client is None:
        _client = MilvusClient(uri=MILVUS_URI)
    return _client


def _collection_embedding_dim(client: MilvusClient) -> int | None:
    """读取已有集合中 embedding 字段维度，读不到返回 None。"""
    try:
        info = client.describe_collection(MILVUS_COLLECTION)
        fields = info.get("fields") if isinstance(info, dict) else getattr(info, "fields", [])
        for field in fields or []:
            name = field.get("name") if isinstance(field, dict) else getattr(field, "name", None)
            if name != "embedding":
                continue
            params = field.get("params") if isinstance(field, dict) else getattr(field, "params", {}) or {}
            dim = params.get("dim") if isinstance(params, dict) else None
            return int(dim) if dim is not None else None
    except Exception:
        return None
    return None


def ensure_collection() -> None:
    """
    确保 document_chunks 集合存在。
    若已存在但向量维度与当前配置不一致，则删除后重建。
    """
    #单下划线开头表示「内部实现，别当公开 API 用」。
    client = _get_client()
    if client.has_collection(MILVUS_COLLECTION):
        #获取向量维度dim的值
        existing_dim = _collection_embedding_dim(client)
        # 仅在明确读到维度且不匹配时重建；读不到则沿用现有集合
        if existing_dim is None or existing_dim == EMBEDDING_DIM:
            return
        client.drop_collection(MILVUS_COLLECTION)
    # 创建集合，创建字段，字段自己创建定义，必须要有向量字段才可以做向量检索，向量字段要指定dim
    schema = MilvusClient.create_schema(auto_id=True, enable_dynamic_field=False)
    schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True)
    schema.add_field(field_name="document_id", datatype=DataType.INT64)
    schema.add_field(field_name="chunk_index", datatype=DataType.INT32)
    schema.add_field(
        field_name="content",
        datatype=DataType.VARCHAR,
        max_length=MILVUS_CONTENT_MAX_LEN,
    )
    schema.add_field(field_name="title", datatype=DataType.VARCHAR, max_length=512)
    schema.add_field(field_name="file_name", datatype=DataType.VARCHAR, max_length=512)
    schema.add_field(
        field_name="embedding",
        datatype=DataType.FLOAT_VECTOR,
        dim=EMBEDDING_DIM,
    )

    index_params = MilvusClient.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="AUTOINDEX",
        metric_type=MILVUS_METRIC_TYPE,
    )

    client.create_collection(
        collection_name=MILVUS_COLLECTION,
        schema=schema,
        index_params=index_params,
    )


def delete_document_vectors(document_id: int) -> None:
    """
    按 document_id 删除 Milvus 中该文档的全部分片向量。
    文档不存在向量时静默成功。
    """
    if document_id <= 0:
        return

    client = _get_client()
    ensure_collection()
    client.delete(
        collection_name=MILVUS_COLLECTION,
        filter=f"document_id == {int(document_id)}",
    )


def _clip_content(text: str) -> str:
    """截断超长 content，避免超出 VARCHAR 上限。"""
    content = (text or "").strip()
    if len(content) <= MILVUS_CONTENT_MAX_LEN:
        return content
    return content[: MILVUS_CONTENT_MAX_LEN - 3] + "..."


def store_document_chunks(
        *,
        document_id: int,
        title: str,
        file_name: str,
        chunks: list[str],
) -> int:
    """
    将文档分片 embedding 后写入 Milvus。
    写入前先删除该 document_id 旧向量，保证重解析幂等。

    :return: 实际写入的分片数量
    """
    if document_id <= 0:
        raise ValueError("document_id 无效")
    if not chunks:
        return 0

    ensure_collection()
    delete_document_vectors(document_id)

    safe_title = (title or "")[:512]
    safe_file_name = (file_name or "")[:512]
    clipped_chunks = [_clip_content(chunk) for chunk in chunks if chunk and chunk.strip()]
    if not clipped_chunks:
        return 0

    vectors = embed_texts(clipped_chunks)
    rows = [
        {
            "document_id": int(document_id),
            "chunk_index": index,
            "content": clipped_chunks[index],
            "title": safe_title,
            "file_name": safe_file_name,
            "embedding": vectors[index],
        }
        for index in range(len(clipped_chunks))
    ]

    client = _get_client()
    client.insert(collection_name=MILVUS_COLLECTION, data=rows)
    client.flush(MILVUS_COLLECTION)
    return len(rows)


def search_document_chunks(
        query: str,
        *,
        top_k: int = RAG_TOP_K,
        document_id: int | None = None,
        score_threshold: float = RAG_SCORE_THRESHOLD,
) -> list[dict]:
    """
    按问题向量检索相关文档分片。

    :param query: 用户问题
    :param top_k: 返回条数上限
    :param document_id: 可选，限定在某一文档内检索
    :param score_threshold: COSINE 相似度下限
    :return: [{content, title, file_name, document_id, chunk_index, score}, ...]
    """
    text = (query or "").strip()
    if not text:
        return []

    # 召回条数兜底，防止过大拖垮上下文
    limit = top_k if top_k and top_k > 0 else RAG_TOP_K
    limit = min(limit, 20)

    # 保证milvus的集合存在
    ensure_collection()
    # 将用户问题转变为向量
    vectors = embed_texts([text])
    if not vectors:
        return []

    client = _get_client()
    search_kwargs = {
        "collection_name": MILVUS_COLLECTION,
        "data": [vectors[0]],
        "limit": limit,
        "output_fields": ["document_id", "chunk_index", "content", "title", "file_name"],
        "search_params": {"metric_type": MILVUS_METRIC_TYPE},
    }
    # 限定单文档问答时只检索该 document_id
    if document_id is not None and int(document_id) > 0:
        search_kwargs["filter"] = f"document_id == {int(document_id)}"

    raw_hits = client.search(**search_kwargs)

    # pymilvus 返回 [[hit, ...]] 或直接 list
    hits = raw_hits[0] if raw_hits and isinstance(raw_hits[0], list) else (raw_hits or [])
    results: list[dict] = []
    for hit in hits:
        if isinstance(hit, dict):
            entity = hit.get("entity") or hit
            #取这条命中结果的相似度得分
            score = float(hit.get("distance", hit.get("score", 0)) or 0)
        else:
            entity = getattr(hit, "entity", None) or {}
            score = float(getattr(hit, "distance", getattr(hit, "score", 0)) or 0)
            if hasattr(entity, "to_dict"):
                entity = entity.to_dict()
            elif not isinstance(entity, dict):
                entity = {
                    "document_id": getattr(entity, "document_id", None),
                    "chunk_index": getattr(entity, "chunk_index", None),
                    "content": getattr(entity, "content", ""),
                    "title": getattr(entity, "title", ""),
                    "file_name": getattr(entity, "file_name", ""),
                }

        # COSINE 越高越相似；过滤低相关分片
        if score < score_threshold:
            continue

        content = str(entity.get("content") or "").strip()
        if not content:
            continue

        results.append(
            {
                "document_id": int(entity.get("document_id") or 0),
                "chunk_index": int(entity.get("chunk_index") or 0),
                "content": content,
                "title": str(entity.get("title") or ""),
                "file_name": str(entity.get("file_name") or ""),
                "score": round(score, 4),
            }
        )

    return results

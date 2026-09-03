"""
RAG 检索与对话记忆配置。
"""

# 向量召回条数上限
RAG_TOP_K = 5

# COSINE 相似度下限（0~1），低于此分的分片不进入上下文
RAG_SCORE_THRESHOLD = 0.35

# 注入 prompt 的单条 chunk 最大字符数
RAG_CHUNK_MAX_CHARS = 800

# 对话记忆：最多保留的消息条数（user+assistant 合计，持久化在 MySQL）
CHAT_MEMORY_MAX_MESSAGES = 12

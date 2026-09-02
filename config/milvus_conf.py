"""
Milvus 向量库连接与 Collection 配置。
文档分片向量写入 document_chunks 集合。
"""

# Milvus Standalone 地址（与 MySQL/MinIO 同机时可共用 IP）
MILVUS_HOST = "203.195.243.93"
MILVUS_PORT = "19530"
MILVUS_URI = f"http://{MILVUS_HOST}:{MILVUS_PORT}"

# 文档分片向量集合名
MILVUS_COLLECTION = "document_chunks"

# 向量维度，需与 text-embedding-v4 输出一致（默认 1024）
EMBEDDING_DIM = 1024

# 向量相似度度量：COSINE 适用于归一化后的 embedding
MILVUS_METRIC_TYPE = "COSINE"

# chunk 正文写入 Milvus VARCHAR 字段的最大长度
MILVUS_CONTENT_MAX_LEN = 4096

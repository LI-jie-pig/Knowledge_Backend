"""
文本 Embedding 配置。
通过阿里云百炼（DashScope）OpenAI 兼容接口调用 text-embedding-v4。
"""
import os

# 百炼 OpenAI 兼容地址（北京地域）
DASHSCOPE_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_API_KEY = os.getenv(
    "DASHSCOPE_API_KEY",
    "sk-ws-H.PMHIILE.ZWjY.MEUCIQCi9rADISBm0IRwuKuOnAGACLoHaOhcPyS6RCooAAgs0AIgTNeMUGQyFEQRSww60i-yaU8LWLBa1K6WKhjskcMxjRw",
).strip()

# Embedding 模型
EMBEDDING_MODEL = "text-embedding-v4"

# text-embedding-v4 默认维度 1024（可选：2048/1536/1024/768/512/256/128/64）
EMBEDDING_DIM = 1024

# v4 单次最多 10 条
EMBEDDING_BATCH_SIZE = 10

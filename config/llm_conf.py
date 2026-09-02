"""
大模型（DeepSeek）调用配置。
通过 OpenAI 兼容接口调用 deepseek-v4-flash。
"""
import os

# DeepSeek OpenAI 兼容地址
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com").strip()
DEEPSEEK_API_KEY = os.getenv(
    "DEEPSEEK_API_KEY",
    "sk-303596e69de240c58c230b72eacd2085",
).strip()

# 对话模型
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash").strip()

# 生成参数
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 2048

# V4 默认开启 thinking，RAG 问答关闭以降低延迟与费用
LLM_THINKING_ENABLED = False

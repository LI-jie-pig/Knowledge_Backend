"""
文档解析与分片配置。
用于控制预览截断长度、chunk 大小等解析参数。
"""

# 详情页预览文本最大字符数
PREVIEW_MAX_CHARS = 2000

# 按字符切分的分片大小与重叠
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# 解析失败原因写入 DB 时的最大长度（对齐 parse_error 字段）
PARSE_ERROR_MAX_LEN = 500

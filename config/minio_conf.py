"""
MinIO 对象存储配置与客户端初始化。
用于文档上传等文件落盘场景。
"""
from minio import Minio
from minio.error import S3Error

# MinIO 连接信息（与现有 db/redis 配置风格一致，按实际环境修改）
MINIO_ENDPOINT = "203.195.243.93:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "Admin@123456"
MINIO_SECURE = False# 本地/内网一般走 http
MINIO_BUCKET = "knowledge-images"
# 对外可访问的基础地址，拼接到 object_name 形成 file_path
MINIO_PUBLIC_BASE = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}"

# 允许上传的扩展名与对应 MIME
ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "markdown"}
EXT_CONTENT_TYPE = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "md": "text/markdown",
    "markdown": "text/markdown",
}
# 单文件大小上限：50MB
MAX_FILE_SIZE = 50 * 1024 * 1024

minio_client = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)


def ensure_bucket() -> None:
    """确保存储桶存在，不存在则创建。"""
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)
    except S3Error as e:
        raise RuntimeError(f"MinIO 桶初始化失败: {e}") from e

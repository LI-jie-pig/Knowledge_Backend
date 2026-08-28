from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func, String, Float, select, Integer, BigInteger, Text
from datetime import datetime

class Base(DeclarativeBase):
    # Mapped[datetime]类型注解，告诉 SQLAlchemy：这个字段 Python 层面是 datetime 对象
    # mapped_column函数，告诉 SQLAlchemy：这个字段在数据库层面是 datetime 类型，且默认值为当前时间
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键")
    created_at: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(), default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now(), default=func.now(), comment="更新时间")
class DocumentCategory(Base):
    __tablename__ = "document_category"
    name: Mapped[str] = mapped_column(String(50), comment="分类名称", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, comment="排序", nullable=False)
    # repr方法，类似java的toString方法，
    # 告诉 SQLAlchemy：这个类的字符串表示为<NewsCategory(id=self.id),name=self.name,sort_order=self.sort_order>
    def __repr__(self):
        return f"<DocumentCategory(id={self.id}),name={self.name},sort_order={self.sort_order}>"
class Document(Base):
    __tablename__ = "document"
    user_id: Mapped[int] = mapped_column(Integer, comment='上传用户ID')
    category_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="分类ID")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="文档标题")
    description: Mapped[str] = mapped_column(String(500), nullable=False, comment="文档描述")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始文件名")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="文件存储路径")
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="文件大小（字节）")
    file_type: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="MIME类型，如application/pdf")
    file_ext: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="文件扩展名，如pdf、txt、md")
    status: Mapped[int] = mapped_column(Integer, nullable=False, comment="处理状态: 0待解析 1解析中 2已完成")
    preview_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="解析后的文本预览")
    parse_error: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="解析失败原因")
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, comment="分片数量(RAG用)")
    upload_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False, comment="上传时间")
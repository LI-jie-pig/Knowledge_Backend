from typing import Optional

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func, String, Float, select, Integer, Index
from datetime import datetime

class Base(DeclarativeBase):
    # Mapped[datetime]类型注解，告诉 SQLAlchemy：这个字段 Python 层面是 datetime 对象
    # mapped_column函数，告诉 SQLAlchemy：这个字段在数据库层面是 datetime 类型，且默认值为当前时间
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键")
    created_at: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(), default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now(), default=func.now(), comment="更新时间")

class News(Base):
    __tablename__="news"
    #创建索引
    __table_args_= (
        Index("idx_category_id", "category_id"),
        Index("idx_publish_time", "publish_time")
    )
    title: Mapped[str] = mapped_column(String(1024),nullable=True, comment='新闻标题')
    description: Mapped[str] = mapped_column(String(1024),nullable=True, comment='新闻描述')
    content: Mapped[str] = mapped_column(String(1024), nullable=True, comment='正文')
    image: Mapped[Optional[str]] = mapped_column(String(255), comment="封面图片URL")
    author: Mapped[Optional[str]] = mapped_column(String(50), comment="作者")
    category_id: Mapped[int] = mapped_column(Integer, nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment='点击量')
    publish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now,comment='发布时间')
    def __repr__(self):
        return f"News<id:{self.id}, title:{self.title}, views:{self.views}>"
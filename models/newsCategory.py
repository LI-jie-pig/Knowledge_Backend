from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func, String, Float, select, Integer
from datetime import datetime

class Base(DeclarativeBase):
    # Mapped[datetime]类型注解，告诉 SQLAlchemy：这个字段 Python 层面是 datetime 对象
    # mapped_column函数，告诉 SQLAlchemy：这个字段在数据库层面是 datetime 类型，且默认值为当前时间
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键")
    created_at: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(), default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now(), default=func.now(), comment="更新时间")
class NewsCategory(Base):
    __tablename__ = "news_category"
    name: Mapped[str] = mapped_column(String(50), comment="分类名称", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, comment="排序", nullable=False)
    # repr方法，类似java的toString方法，
    # 告诉 SQLAlchemy：这个类的字符串表示为<NewsCategory(id=self.id),name=self.name,sort_order=self.sort_order>
    def __repr__(self):
        return f"<Category(id={self.id}),name={self.name},sort_order={self.sort_order}>"
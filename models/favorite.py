from datetime import datetime
from sqlalchemy import UniqueConstraint, Index, Integer, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from models.news import News
from models.user import User


class Base(DeclarativeBase):
    pass


class Favorite(Base):
    """
    收藏表ORM模型
    """
    __tablename__ = 'favorite'

    # 创建索引、唯一约束
    __table_args__ = (
        UniqueConstraint('user_id', 'news_id', name='user_news_unique'),
        Index('fk_favorite_user_idx', 'user_id'),
        Index('fk_favorite_news_idx', 'news_id'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), nullable=False)
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey(News.id), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, news_id={self.news_id})>"

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass
class History(Base):
    __tablename__ = 'history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    news_id: Mapped[int] = mapped_column(Integer, nullable=False)
    view_time: Mapped[datetime] = mapped_column(DateTime)
    def __repr__(self):
        return f"<History(id={self.id}, user_id={self.user_id}, news_id={self.news_id})>"
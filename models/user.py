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

class User(Base):
    __tablename__ = 'user'
    username: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户名")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码（bcrypt加密）")
    nickname: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="昵称")
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="头像URL")
    gender: Mapped[Optional[str]] = mapped_column(
        nullable=True,
        comment="性别"
    )
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="个人简介")
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="手机号")
    def __repr__(self):
        return f"user<id:{self.id},username:{self.username}"
class UserToken(Base):
    __tablename__ = 'user_token'
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="用户ID")
    token: Mapped[str] = mapped_column(String(255), nullable=False, comment="令牌")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")

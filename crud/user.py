from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from utils.security import get_password_hash


async def select_user_by_username(
        db: AsyncSession,
        user_name: str
):
    result = await db.execute(select(User).where(User.username == user_name))
    return result.scalar_one_or_none()
async def create_user(
        db: AsyncSession,
        user: object
):
    #密码加密
    password = get_password_hash(user.password)
    user = User(username=user.username, password=password)#类似java的构造函数
    db.add(user)
    await db.commit()
    await db.refresh(user) #从数据库读取最新的user
    return user
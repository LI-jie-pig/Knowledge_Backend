import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException, Request

from sqlalchemy.ext.asyncio import AsyncSession, result
from sqlalchemy import select, update
from models.user import User, UserToken
from schemas.user import UserInfoRequest
from utils.security import get_password_hash, verify_password


async def select_user_by_username(
        db: AsyncSession,
        user_name: str
):
    result = await db.execute(select(User).where(User.username == user_name))
    return result.scalar_one_or_none()
async def select_user_by_userid(
        db: AsyncSession,
        token: str
):
    token_info = (await db.execute(select(UserToken).where(UserToken.token == token))).scalar_one_or_none()
    if not token_info or token_info.expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    result = await db.execute(select(User).where(User.id == token_info.user_id))
    return result.scalar_one_or_none()


async def create_user(
        db: AsyncSession,
        user: object
):
    #密码加密
    password = get_password_hash(user.password)
    user = User(username=user.username, password=password, nickname = user.nickname)#类似java的构造函数
    db.add(user)
    await db.commit()
    await db.refresh(user) #从数据库读取最新的user
    return user
async def create_token(
        db: AsyncSession,
        user_id: int
):
    #生成token + 设置过期时间 -> 查询当前数据库的用户是否有token -> 有:则更新;没有:则添加
    token = str(uuid.uuid4())
    #timedelta(days=7, hours=2, minutes=30, seconds=30)表示时间间隔
    expired_at = datetime.now() + timedelta(days=7)
    user = (await db.execute(select(UserToken).where(UserToken.user_id == user_id))).scalar_one_or_none()
    if not user:
        userToken = UserToken(user_id=user_id, token=token, expires_at=expired_at)
        db.add(userToken)
        await db.commit()
    else:
        await db.execute(update(UserToken).where(UserToken.user_id == user_id).values(token=token, expires_at=expired_at))
        await db.commit()
    return token
async def login_user(
        db: AsyncSession,
        user: object
):
    user_true = (await db.execute(select(User).where(User.username == user.username))).scalar_one_or_none()
    if not user_true:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(user.password, user_true.password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    return user_true

async def update_info(
        user_info: UserInfoRequest,
        user_id: int,
        db: AsyncSession
):
    # await db.execute(update(User).where(User.id == user_id).values({**[item for item in user_info.__dict__ if item is not None]}))
    result = await db.execute(update(User).where(User.id == user_id).values({**user_info.model_dump(
        exclude_unset=True,
        exclude_none=True
    )}))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await db.commit()
    user_true = await db.execute(select(User).where(User.id == user_id))
    return user_true.scalar_one_or_none()
async def change_password(
        user: User,
        old_password: str,
        new_password: str,
        db: AsyncSession
):
    result_user = (await db.execute(select(User).where(User.id == user.id))).scalar_one_or_none()
    if not verify_password(old_password, result_user.password):
        raise HTTPException(status_code=400, detail="密码错误,不能修改密码")
    password_string = get_password_hash(new_password)
    await db.execute(update(User).where(User.id == user.id).values(password = password_string))
    await db.commit()
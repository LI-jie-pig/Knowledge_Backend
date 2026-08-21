#根据token查询用户，返回用户信息
from fastapi import Header
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import select_user_by_userid
from config.db_conf import get_database


async def get_user_by_token(
        token: str = Header(..., alias="Authorization"),
        db: AsyncSession = Depends(get_database)
):
    token = token.replace("Bearer ", "")
    return await select_user_by_userid(db, token)

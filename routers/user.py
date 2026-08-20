from http.client import HTTPException

from fastapi import APIRouter
from fastapi import Depends
from config.db_conf import get_database
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import select_user_by_username, create_user
from schemas.user import UserRequest

router = APIRouter(prefix="/api/user", tags=["user"])

@router.post("/register")
async def register(
        user: UserRequest,
        db: AsyncSession = Depends(get_database),
):
    exist_user = await select_user_by_username(db, user.username)
    if exist_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    new_user = await create_user(db, user)
    return {
        "code":200,
        "message":"用户注册成功",
        "data": new_user
    }

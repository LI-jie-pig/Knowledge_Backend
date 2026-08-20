from fastapi import APIRouter
from fastapi import Depends
from config.db_conf import get_database
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.user import UserRequest

router = APIRouter(prefix="/api/user", tags=["user"])

@router.post("/register")
async def register(
        user: UserRequest,
        db: AsyncSession = Depends(get_database),
):
    return {
        "code":200,
        "message":"获取新闻分类成功",
        "data": ""
    }

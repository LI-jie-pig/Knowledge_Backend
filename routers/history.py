from unittest import result

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_database
from crud.favorite import select_favorite_list
from crud.history import add_history_info, select_history_list
from models.history import History
from models.user import User
from schemas.history import HistoryAddResponse
from utils.auth import get_user_by_token
from utils.response import success_response

router = APIRouter(prefix="/api/history", tags=["history"])
@router.post("/add")
async def add_history(
    history: HistoryAddResponse,
    db: AsyncSession = Depends(get_database),
    user: User = Depends(get_user_by_token)
):
    result_info = await add_history_info(history, db, user)
    return success_response(data=history.news_id, message="历史记录添加成功")
@router.get("/list")
async def get_history_list(
    page:int,
    page_size: int = Query(10, gt=0, alias="pageSize"),
    db: AsyncSession = Depends(get_database),
    user: User = Depends(get_user_by_token)
):
    history_list, total = await select_history_list(db, user, page, page_size)
    data_list = [{
        "id": history[1].id,
        "title": history[1].title,
        "content": history[1].content,
        "description": history[1].description,
        "image": history[1].image,
        "author": history[1].author,
        "views": history[1].views,
        "view_time": history[0].view_time
    } for history in history_list]
    return success_response(data={"list": data_list, "total": total, "hasMore": total > page_size * page}, message="历史记录查询成功")

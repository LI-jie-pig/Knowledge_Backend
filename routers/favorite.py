from fastapi import APIRouter,Query
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_database
from crud.favorite import is_news_favorite, add_favorite_news, remove_favorite, select_favorite_list, \
    favorite_list_count, remove_all_favorite
from models.user import User
from schemas.favorite import FavoriteCheckResponse, FavoriteAddResponse, FavoriteListResponse
from utils.auth import get_user_by_token
from utils.response import success_response

router = APIRouter(prefix="/api/favorite", tags=["favorite"])

@router.get("/check")
async def check_favorite(
        news_id : int =Query(..., description="新闻ID", alias="newsId"),
        db: AsyncSession = Depends(get_database),
        user: User = Depends(get_user_by_token)
):
    return success_response(data=FavoriteCheckResponse(isFavorite = await is_news_favorite(news_id, user.id, db)))

@router.post("/add")
async def add_favorite(
    add_favorite_request: FavoriteAddResponse,
    db: AsyncSession = Depends(get_database),
    user: User = Depends(get_user_by_token)
):
    result = await add_favorite_news(add_favorite_request, db, user)
    return success_response(data=FavoriteAddResponse(newsId = add_favorite_request.news_id))
@router.delete("/remove")
async def remove(
    news_id: int =Query(..., description="新闻ID", alias="newsId"),
    db: AsyncSession = Depends(get_database),
    user: User = Depends(get_user_by_token)
):
    result = await remove_favorite(news_id, user, db)
    if not result:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return success_response(data = result, message="取消收藏成功")
@router.get("/list")
async def list_favorite(
    page: int = Query(1, description="页码", alias="page"),
    page_size: int = Query(10, description="每页数量", alias="pageSize"),
    db: AsyncSession = Depends(get_database),
    user: User = Depends(get_user_by_token)
):
    result = await select_favorite_list(page, page_size, user, db)
    count = await favorite_list_count(user, db)
    return success_response(data={"list":result,"total":count, "hasMore":count > len(result)})
@router.delete("/clear")
async def clear_favorite(
    db: AsyncSession = Depends(get_database),
    user: User = Depends(get_user_by_token)
):
    result = await remove_all_favorite(user, db)
    if not result:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return success_response(data = result, message="清空收藏成功")

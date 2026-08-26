from http.client import HTTPException

from fastapi import APIRouter, Depends,Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from cache.news_cache import set_cache_categories, get_news_categories_cache, get_news_cache, set_news_cache
from config.db_conf import get_database

from sqlalchemy import DateTime, func, String, Float, select, Integer, update

from models.news import News
from models.newsCategory import NewsCategory

def page_params(skip: int = Query(0, gt=0), limit: int = Query(10, ge=0,le=100)):
    return {"skip": skip, "limit": limit}

async def get_news_categories(
        db: AsyncSession,
):
    cache = await get_news_categories_cache()
    if cache:
        return cache
    result = await db.execute(select(NewsCategory))
    categories = result.scalars().all()
    if categories:
        categories = jsonable_encoder(categories)
        await set_cache_categories(categories)
    return categories

async def get_news_list(
        db: AsyncSession,
        category_id: int,
        page: int,
        page_size:int
        ):
    cache_result = await get_news_cache(category_id, page, page_size)
    if cache_result:
        # return [News(**item) for item in cache_result]
        return cache_result
    params = {"skip": (page-1) * page_size, "limit": page_size, "category_id": category_id}
    result = await db.execute(select(News).where(News.category_id == params["category_id"]).order_by(News.created_at.desc()).offset(params["skip"]).limit(params["limit"]))
    result_list = result.scalars().all()
    if result_list:
        result_list = jsonable_encoder(result_list)  #将ORM对象转换为Python原生的可序列化对象
        # news_data = [NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False) for item in result_list]
        await set_news_cache(category_id, page, page_size, result_list)
    return result_list
async def get_news_total(
        db: AsyncSession,
        category_id: int
        ):
    result = await db.execute(select(func.count(News.id)).where(News.category_id == category_id))
    return result.scalar_one()
async def detail_info(
        db: AsyncSession,
        news_id: int
        ):
    result = await db.execute(select(News).where(News.id == news_id))
    return result.scalar_one_or_none()
async def increase_news_view(
        db: AsyncSession,
        news_id: int
):
    stmt = update(News).where(News.id == news_id).values(views=News.views+1)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount >0
async def select_related_news(
        db: AsyncSession,
        news: object
):
    #order_by 排序
    result = await db.execute(select(News).where((News.category_id == news.category_id) & (News.id != news.id)).order_by(News.views.desc()).limit(3))
    news =  result.scalars().all()
    #列表推导式,返回核心数据
    return [{
        "id": new.id,
        "title": new.title,
        "description": new.description,
        "created_at": new.created_at,
        "views": new.views
    } for new in news]
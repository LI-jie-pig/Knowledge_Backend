from http.client import HTTPException

from fastapi import APIRouter, Depends,Query
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_conf import get_database

from sqlalchemy import DateTime, func, String, Float, select, Integer, update

from models.news import News
from models.newsCategory import NewsCategory

def page_params(skip: int = Query(0, gt=0), limit: int = Query(10, ge=0,le=100)):
    return {"skip": skip, "limit": limit}
async def get_news_categories(
        db: AsyncSession,
        ):
    result = await db.execute(select(NewsCategory))
    return result.scalars().all()
async def get_news_list(
        db: AsyncSession,
        category_id: int,
        page: int,
        page_size:int
        ):
    params = {"skip": (page-1) * page_size, "limit": page_size, "category_id": category_id}
    result = await db.execute(select(News).where(News.category_id == params["category_id"]).order_by(News.created_at.desc()).offset(params["skip"]).limit(params["limit"]))
    return result.scalars().all()
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
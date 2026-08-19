from fastapi import APIRouter, Depends,Query
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_conf import get_database

from sqlalchemy import DateTime, func, String, Float, select, Integer

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
    params = {"skip": page * page_size, "limit": page_size, "category_id": category_id}
    result = await db.execute(select(News).where(News.category_id == params["category_id"]).offset(params["skip"]).limit(params["limit"]))
    return result.scalars().all()
async def get_news_total(
        db: AsyncSession,
        category_id: int
        ):
    result = await db.execute(select(func.sum(News.id)).where(News.category_id == category_id))
    return result.scalar()
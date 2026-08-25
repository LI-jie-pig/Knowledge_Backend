from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News
from models.user import User
from schemas.favorite import FavoriteAddResponse


async def is_news_favorite(
        news_id :int,
        user_id :int,
        db: AsyncSession
):
    result = await db.execute(select(Favorite).where((Favorite.user_id == user_id) & (Favorite.news_id == news_id)))
    return result.scalar_one_or_none() is not None
async def add_favorite_news(
    news_response: FavoriteAddResponse,
    db: AsyncSession,
    user: User
):
    db.add(Favorite(user_id=user.id, news_id=news_response.news_id))
    await db.commit()
    return True
async def remove_favorite(news_id: int, user: User, db: AsyncSession):
    result = await db.execute(delete(Favorite).where(Favorite.user_id == user.id, Favorite.news_id == news_id))
    await db.commit()
    return result.rowcount > 0
async def remove_all_favorite(user: User, db: AsyncSession):
    result = await db.execute(delete(Favorite).where(Favorite.user_id == user.id))
    await db.commit()
    return result.rowcount > 0
async def select_favorite_list(
    page: int,
    page_size: int,
    user: User,
    db: AsyncSession
):
    result = await db.execute(select(Favorite).where(Favorite.user_id == user.id).offset(((page-1) * page_size)).limit(page_size))
    favorite_list = result.scalars().all()
    news_list = await db.execute(select(News).where(News.id.in_([favorite.news_id for favorite in favorite_list])))
    # 连表查询
    list_info = await db.execute(select(News, Favorite.created_at.label("favorite_time"), Favorite.id.label("favorite_id"))
     .join(Favorite, Favorite.news_id == News.id)
     .where(Favorite.user_id == user.id)
     .order_by(Favorite.created_at.desc())
     .offset(((page-1) * page_size))
     .limit(page_size)
     )
    # return news_list.scalars().all()
    return list_info.scalars().all()
async def favorite_list_count(user: User, db: AsyncSession):
    return (await db.execute(select(func.count(Favorite.id)).where(Favorite.user_id == user.id))).scalar_one()
from datetime import datetime
from unittest import result

from click import DateTime
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.history import History
from models.news import News
from models.user import User
from schemas.history import HistoryAddResponse


async def add_history_info(
        history: HistoryAddResponse,
        db: AsyncSession,
        user: User
):
    result = await db.execute(select(History).where(History.user_id == user.id, History.news_id == history.news_id))
    if result.scalar_one_or_none() is not None:
        await db.execute(update(History).where(History.user_id == user.id, History.news_id == history.news_id).values(view_time=datetime.now()))
        await db.commit()
    else:
        history_true = History(user_id=user.id, news_id=history.news_id, view_time=datetime.now())
        db.add(history_true)
        await db.commit()
    return True

async def select_history_list(
        db: AsyncSession,
        user: User,
        page: int,
        page_size: int
):
    result = await db.execute(select(History,News).join(News, History.news_id == News.id).where(History.user_id == user.id).order_by(History.view_time.desc()).offset((page-1) * page_size).limit(page_size))
    total = await db.execute(select(func.count(History.id)).where(History.user_id == user.id))
    return result.all(), total.scalar_one()

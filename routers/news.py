from datetime import datetime
from fastapi import APIRouter, Depends,Query
from sqlalchemy import DateTime, func, String, Float, select, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config.db_conf import get_database
from crud import news

#创建APIRouter实例
router = APIRouter(prefix="/api/news", tags=["news"])
# def page_params(skip: int = Query(0, gt=0), limit: int = Query(10, ge=0,le=100)):
#     return {"skip": skip, "limit": limit}
# class Base(DeclarativeBase):
#     # Mapped[datetime]类型注解，告诉 SQLAlchemy：这个字段 Python 层面是 datetime 对象
#     # mapped_column函数，告诉 SQLAlchemy：这个字段在数据库层面是 datetime 类型，且默认值为当前时间
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键")
#     created_at: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(), default=func.now(), comment="创建时间")
#     updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now(), default=func.now(), comment="更新时间")
# class NewsCategory(Base):
#     __tablename__ = "news_category"
#     name: Mapped[str] = mapped_column(String(50), comment="分类名称")
#     sort_order: Mapped[int] = mapped_column(Integer, comment="排序")
#
# @router.get("/categories")
# async def get_news_categories(
#         params: dict = Depends(page_params),
#         db = Depends(get_database)):
#     result = await db.execute(select(NewsCategory))
#     return result.scalars().all()
# 接口的实现：1.模块化路由 2.定义模型类 -> 数据库表
# 3.在crud目录下创建文件，封装操作数据库方法   4.在路由处理函数中调crud封装好的方法，响应结果
@router.get("/categories")
async def get_news_categories(db: AsyncSession = Depends(get_database)):
    return {
        "code":200,
        "message":"获取新闻分类成功",
        "data": await news.get_news_categories(db)
    }
@router.get("/list")
async def get_news_list(
        db: AsyncSession = Depends(get_database),
        category_id: int = Query(None, alias="categoryId"),
        page: int = Query(0, gt=0, alias="page"),
        page_size: int = Query(10, ge=0,le=100, alias="pageSize")
):
    return {
        "code":200,
        "message":"获取新闻列表成功",
        "data": {"list": await news.get_news_list(db, category_id, page, page_size),
                 "total": await news.get_news_total(db, category_id),
                 "hasMore": False
                 }
    }


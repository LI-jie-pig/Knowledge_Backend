#新闻相关的缓存方法:新闻分类的读取和写入
#key - value

from config.cache_conf import get_json_cache, set_cache
from typing import List, Dict, Any
CATEGORIES_KEY = "news:categories"
NEWS_KEY = "news:news:{category}:{size}:{size_page}"
#写入新闻缓存
async def set_news_cache(
    category_id: int,
    size:int,
    size_page: int,
    data: List[Dict[str, Any]],
    expire: int = 1600
):
    key = NEWS_KEY.format(category=category_id, size=size, size_page=size_page)
    return await set_cache(key, data, expire)
#读取新闻缓存
async def get_news_cache(
    category_id: int,
    size:int,
    size_page: int
):
    key = NEWS_KEY.format(category=category_id, size=size, size_page=size_page)
    return await get_json_cache(key)


#获取新闻分类缓存
async def get_news_categories_cache(

):
    return await get_json_cache(CATEGORIES_KEY)
#写入新闻分类缓存:缓存的数据，过期时间
async def set_cache_categories(
    data: List[Dict[str, Any]],
    expire: int = 7200
):
    return await set_cache(CATEGORIES_KEY, data, expire)
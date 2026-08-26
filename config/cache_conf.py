import json
from redis.asyncio import ConnectionPool

import redis.asyncio
REDIS_HOST = "localhost"
#创建redis的连接对象
pool = ConnectionPool(
    host=REDIS_HOST,
    port=6379,
    db=1,
    protocol=2,   # 放到连接池！！
    decode_responses=True,#自动将返回值解码为字符串
    socket_timeout=5
)
redis_client = redis.asyncio.Redis(
    connection_pool=pool
)
#设置和读取字符串，读取列表或字典
#读取字符串
async def get_cache(
    key: str
):
    try:
        return await redis_client.get(key)
    except Exception as e:
        print(f"Error reading from cache: {e}")
        return None
#读取列表或字典
async def get_json_cache(
    key: str
):
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        print(f"Error reading from json cache: {e}")
        return None
#设置缓存
async def set_cache(
    key: str,
    value: str,
    expire: int = 3600
):
    try:
        if isinstance(value, (dict,list)):
            #转字符串再存
            value = json.dumps(value, ensure_ascii=False)
        await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        print("设置缓存失败",e)
        return False
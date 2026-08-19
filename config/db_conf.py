from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, result

#1.创建异步引擎
ASYNC_DATABASE_URL = "mysql+aiomysql://root:lgxlgx945@localhost:3306/knowledge_backend?charset=utf8mb4"
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo = True, # 开启日志打印
    pool_size=10, # 连接池大小
    max_overflow=20 # 连接池最大溢出数
)
# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind= async_engine, #绑定数据库引擎
    class_=AsyncSession, #指定会话类
    expire_on_commit=False #指定提交不过期
)
#依赖项
async def get_database():
    async with AsyncSessionLocal() as session:
        try:
            yield session   # 返回数据库会话给路由函数
            await session.commit() #提交事务
        except:
            await session.rollback() # 有异常回滚
            raise Exception("数据库操作异常")
        finally:
            await session.close() #关闭会话
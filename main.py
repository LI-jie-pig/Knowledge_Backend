from fastapi import FastAPI

from routers import news, user
from fastapi.middleware.cors import CORSMiddleware

from utils.exception import register_exception_handlers

app = FastAPI()
#挂载路由
app.include_router(news.router)
app.include_router(user.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许所有来源的请求，生产环境需要指定允许的来源
    allow_credentials=True, # 允许发送Cookie
    allow_methods=["*"], # 允许所有HTTP方法
    allow_headers=["*"], # 允许所有HTTP头
)
register_exception_handlers(app)
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

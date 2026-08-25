
from fastapi import APIRouter,HTTPException
from fastapi import Depends, Query
from config.db_conf import get_database
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import select_user_by_username, create_user, create_token, login_user, update_info, change_password
from models.user import User
from schemas.user import UserRequest, UserAuthResponse, UserInfoResponse, UserInfoRequest, UserChangePassword
from utils.auth import get_user_by_token
from utils.response import success_response

router = APIRouter(prefix="/api/user", tags=["user"])

@router.post("/register")
async def register(
        user: UserRequest,
        db: AsyncSession = Depends(get_database),
):
    exist_user = await select_user_by_username(db, user.username)
    if exist_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    new_user = await create_user(db, user)
    token = await create_token(db, new_user.id)
    data_user = {"userInfo":{**new_user.__dict__}, "token": token}
    # return {
    #     "code":200,
    #     "message":"用户注册成功",
    #     "data": data_user
    # }
    response_data = UserAuthResponse(token= token, userInfo= UserInfoResponse.model_validate(new_user))
    # return success_response(data_user, "用户注册成功")
    return success_response(response_data, "用户注册成功")

@router.post("/login")
async def login(
        user: UserRequest,
        db: AsyncSession = Depends(get_database),
):

    exist_user = await login_user(db, user)
    token = await create_token(db, exist_user.id)
    response_data = UserAuthResponse(token= token, userInfo= UserInfoResponse.model_validate(exist_user))
    return success_response(response_data, "用户登录成功")
@router.get("/info")
async def info(
        db: AsyncSession = Depends(get_database),
        user: User = Depends(get_user_by_token)
):
    return success_response(UserInfoResponse.model_validate(user), "获取用户信息成功")
@router.put("/update")
async def update_user_info(
        user_info: UserInfoRequest,
        db: AsyncSession = Depends(get_database),
        user: User = Depends(get_user_by_token)
):
    user = await update_info(user_info, user.id, db)
    return success_response(UserInfoRequest.model_validate(user), "更新用户信息成功")
@router.put("/password")
async def change_password_user(
        password_list: UserChangePassword,
        user: User = Depends(get_user_by_token),
        db: AsyncSession = Depends(get_database)
):
    await change_password(user, password_list.old_password, password_list.new_password, db)
    return success_response({"message": "密码更新成功"})

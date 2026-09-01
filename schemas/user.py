from pydantic import Field, ConfigDict
from pydantic import BaseModel
from typing import Optional
class UserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=3, max_length=50)
    nickname: str = Field(None, max_length=50)
#user_info 对应的类
class UserInfoBase(BaseModel):
    """用户信息基础数据模型"""
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
class UserInfoResponse(UserInfoBase):
    id: int
    username: str
    #模型类配置
    model_config = ConfigDict(
        from_attributes=True #允许从ORM对象属性获取数据
    )
class UserInfoRequest(UserInfoBase):
    phone: Optional[str] = Field(None, max_length=11, description="手机号")
    model_config = ConfigDict(
        from_attributes=True #允许从ORM对象属性获取数据
    )
# data数据类型
class UserAuthResponse(BaseModel):
    token: str
    user_info: UserInfoResponse = Field(..., alias="userInfo")
    #模型类配置
    model_config = ConfigDict(
        from_attributes=True #允许从ORM对象属性获取数据
    )
class UserChangePassword(BaseModel):
    old_password: str = Field(..., min_length=3, max_length=50, alias="oldPassword")
    new_password: str = Field(..., min_length=3, max_length=50, alias="newPassword")

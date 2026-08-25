
from pydantic import BaseModel, Field, ConfigDict


class FavoriteCheckResponse(BaseModel):
    is_favorite: bool = Field(..., alias="isFavorite")
    #模型类配置
    model_config = ConfigDict(
        from_attributes=True #允许从ORM对象属性获取数据
    )
class FavoriteAddResponse(BaseModel):
    news_id: int = Field(..., alias="newsId")

class FavoriteListResponse(BaseModel):
    list: list[dict]
    total: int
    has_more: bool = Field(alias="hasMore")
    #模型类配置
    model_config = ConfigDict(
        from_attributes=True #允许从ORM对象属性获取数据
    )

from pydantic import BaseModel, Field, ConfigDict
class HistoryAddResponse(BaseModel):
    news_id: int = Field(..., alias="newsId")
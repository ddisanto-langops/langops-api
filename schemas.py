from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from models import TrelloData, YouTubeData, CrowdinData

class CheckHealthResponse(BaseModel):
    status: str = "OK"
    database_version: str


class LangOpsProductResponse(BaseModel):
    id: str
    date_created: datetime
    trello_data: Optional[TrelloData]
    youtube_data: Optional[YouTubeData]
    crowdin_data: Optional[CrowdinData]

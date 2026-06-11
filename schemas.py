from pydantic import BaseModel
from models import TrelloData, YouTubeData, CrowdinData

class CheckHealthResponse(BaseModel):
    status: str = "OK"
    database_version: str


class LangOpsProductResponse(BaseModel):
    id: str
    date_created: str
    trello_data: TrelloData
    youtube_data: YouTubeData
    crowdin_data: CrowdinData

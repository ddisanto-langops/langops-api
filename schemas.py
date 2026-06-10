from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TrelloData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    title: str
    product_code: str = Field(alias="productCode")
    target_language: str = Field(alias="targetLanguage")
    due_date: Optional[datetime] = Field(None, alias="dueDate")
    date_published: Optional[datetime] = Field(None, alias="datePublished")
    date_last_activity: datetime = Field(alias="dateLastActivity")
    media_groups: list[str] = Field(alias="mediaGroups")
    editor_url: Optional[str] = Field(None, alias="editorUrl")
    article_url: Optional[str] = Field(None, alias="articleUrl")
    word_count: Optional[int] = Field(None, alias="wordCount")


class YouTubeData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    localized_title: str = Field(alias="localizedTitle")
    url: str
    duration_seconds: int = Field(alias="durationSeconds")


class CrowdinData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crowdin_id: Optional[str] = Field(None, alias="crowdinId")
    translation_progress: Optional[float] = Field(None, alias="translationProgress")
    approval_progress: Optional[float] = Field(None, alias="approvalProgress")
    crowdin_url: Optional[str] = Field(None, alias="crowdinUrl")



class LangOpsProduct(BaseModel):
    """Represents a product taken from any source of truth,

    across various states (Trello active or archived, YouTube
    published/unpublished).
    Note: the dicts containing Trello, YouTube and Crowdin data
    do not represent raw fetched data, but rather the synthesized and
    aggregated data after fetching has already been performed. A LangOps
    product is the shape that is stored in the database and that the frontend
    sees.
    A LangOps API can be supported in the future if required.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    date_created: datetime = Field(alias="dateCreated")
    trello_data: Optional[TrelloData] = Field(None, alias="trelloData")
    youtube_data: Optional[YouTubeData] = Field(None, alias="youTubeData")
    crowdin_data: Optional[CrowdinData] = Field(None, alias="crowdinData")

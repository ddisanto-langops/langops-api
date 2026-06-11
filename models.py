from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class TrelloData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    title: str
    product_code: str 
    target_language: str
    due_date: Optional[datetime]
    date_published: Optional[datetime]
    date_last_activity: datetime
    media_groups: list[str]
    editor_url: Optional[str]
    article_url: Optional[str]
    word_count: Optional[int]


class YouTubeData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    localized_title: str
    url: str
    duration_seconds: int


class CrowdinData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crowdin_id: Optional[str]
    translation_progress: Optional[float]
    approval_progress: Optional[float]
    crowdin_url: Optional[str]



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
    trello_data: Optional[TrelloData]
    youtube_data: Optional[YouTubeData]
    crowdin_data: Optional[CrowdinData]

class LangOpsProductORM(Base):
    __tablename__ = "langops_products"

    id = Column(String, primary_key=True)
    date_created = Column(DateTime(timezone=True), nullable=False)

    trello_id = Column(String)
    trello_url = Column(String)
    trello_title = Column(String)
    trello_product_code = Column(String)
    trello_target_language = Column(String)
    trello_due_date = Column(DateTime(timezone=True))
    trello_date_published = Column(DateTime(timezone=True))
    trello_date_last_activity = Column(DateTime(timezone=True))
    trello_media_groups = Column(ARRAY(String))
    trello_editor_url = Column(String)
    trello_article_url = Column(String)
    trello_word_count = Column(Integer)

    youtube_id = Column(String)
    youtube_localized_title = Column(String)
    youtube_url = Column(String)
    youtube_duration_seconds = Column(Integer)

    crowdin_id = Column(String)
    crowdin_translation_progress = Column(Float)
    crowdin_approval_progress = Column(Float)
    crowdin_url = Column(String)


def orm_to_langops_product(row: LangOpsProductORM) -> LangOpsProduct:
    trello = TrelloData(
        id=row.trello_id,
        url=row.trello_url,
        title=row.trello_title,
        product_code=row.trello_product_code,
        target_language=row.trello_target_language,
        due_date=row.trello_due_date,
        date_published=row.trello_date_published,
        date_last_activity=row.trello_date_last_activity,
        media_groups=row.trello_media_groups or [],
        editor_url=row.trello_editor_url,
        article_url=row.trello_article_url,
        word_count=row.trello_word_count,
    ) if row.trello_id else None

    youtube = YouTubeData(
        id=row.youtube_id,
        localized_title=row.youtube_localized_title,
        url=row.youtube_url,
        duration_seconds=row.youtube_duration_seconds,
    ) if row.youtube_id else None

    crowdin = CrowdinData(
        crowdin_id=row.crowdin_id,
        translation_progress=row.crowdin_translation_progress,
        approval_progress=row.crowdin_approval_progress,
        crowdin_url=row.crowdin_url,
    ) if row.crowdin_id else None

    return LangOpsProduct(
        id=row.id,
        dateCreated=row.date_created,
        trello_data=trello,
        youtube_data=youtube,
        crowdin_data=crowdin,
    )
from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, UUID as SA_UUID
import uuid
from sqlalchemy.orm import DeclarativeBase
from schemas import TrelloData, YouTubeData, CrowdinData, ProductResponse


class Base(DeclarativeBase):
    pass


class LangOpsProductORM(Base):
    __tablename__ = "langops_products"
    
    id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.UUID)
    date_created = Column(DateTime(timezone=True), nullable=False)
    date_deleted = Column(DateTime(timezone=True), nullable=True)

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


def orm_to_langops_product(row: LangOpsProductORM) :
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

    return ProductResponse(
        id=row.id,
        date_created=row.date_created,
        date_deleted=row.date_deleted,
        trello_data=trello,
        youtube_data=youtube,
        crowdin_data=crowdin,
    )
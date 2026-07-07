from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Float, Integer, DateTime, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID as SA_UUID
from schemas.data_schemas import LangOpsProduct, TrelloData, YouTubeData, CrowdinData


class Base(DeclarativeBase):
    pass


class LangOpsProductORM(Base):
    __tablename__ = "langops_products"
    
    id = Column(SA_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    date_created = Column(DateTime(timezone=True), nullable=False)
    date_deleted = Column(DateTime(timezone=True), nullable=True)
    media_groups = Column(ARRAY(String))
    product_status = Column(String, nullable=False)

    trello_id = Column(String)
    trello_url = Column(String)
    trello_title = Column(String)
    trello_localized_title = Column(String)
    trello_product_code = Column(String)
    trello_target_language = Column(String)
    trello_due_date = Column(DateTime(timezone=True))
    trello_date_published = Column(DateTime(timezone=True))
    trello_date_last_activity = Column(DateTime(timezone=True))
    trello_date_archived = Column(DateTime(timezone=True))
    trello_editor_url = Column(String)
    trello_article_url = Column(String)
    trello_word_count = Column(Integer)

    youtube_id = Column(String)
    youtube_localized_title = Column(String)
    youtube_url = Column(String)
    youtube_duration_seconds = Column(Integer)

    crowdin_file_id = Column(String)
    crowdin_project_id = Column(String)
    crowdin_translation_progress = Column(Float)
    crowdin_approval_progress = Column(Float)
    crowdin_url = Column(String)


def orm_to_langops_product(row: LangOpsProductORM) -> LangOpsProduct:
    trello = TrelloData(
        id=row.trello_id,
        url=row.trello_url,
        title=row.trello_title,
        localized_title=row.trello_localized_title,
        product_code=row.trello_product_code,
        target_language=row.trello_target_language,
        due_date=row.trello_due_date,
        date_published=row.trello_date_published,
        date_last_activity=row.trello_date_last_activity,
        date_archived=row.trello_date_archived,
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
        crowdin_file_id=row.crowdin_file_id,
        crowdin_project_id=row.crowdin_project_id,
        translation_progress=row.crowdin_translation_progress,
        approval_progress=row.crowdin_approval_progress,
        crowdin_url=row.crowdin_url,
    ) if row.crowdin_file_id else None

    return LangOpsProduct(
        id=row.id,
        date_created=row.date_created,
        date_deleted=row.date_deleted,
        media_groups=row.media_groups or [],
        product_status=row.product_status,
        trello_data=trello,
        youtube_data=youtube,
        crowdin_data=crowdin,
    )
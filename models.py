import uuid
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column
from sqlalchemy import ARRAY, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID as SA_UUID
from schemas.data_schemas import LangOpsProduct, NewLangOpsProduct, TrelloData, YouTubeData, CrowdinData


class Base(DeclarativeBase, MappedAsDataclass):
    pass


class LangOpsProductORM(Base):
    __tablename__ = "langops_products"
    
    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID(as_uuid=True), 
        primary_key=True, 
        server_default=text("gen_random_uuid()"),
        init=False # Do not require ID on object creation since server assigns it
    )
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    date_deleted: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    media_groups: Mapped[list[str]] = mapped_column(ARRAY(String))
    product_status: Mapped[str]

    trello_id: Mapped[str]
    trello_url: Mapped[str]
    trello_title: Mapped[str]
    trello_localized_title: Mapped[str | None]
    trello_product_code: Mapped[str | None]
    trello_target_language: Mapped[str | None]
    trello_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trello_date_published: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trello_date_last_activity: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trello_date_archived: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trello_editor_url: Mapped[str | None]
    trello_article_url: Mapped[str | None]
    trello_word_count: Mapped[int | None]

    youtube_id: Mapped[str | None]
    youtube_localized_title: Mapped[str | None]
    youtube_url: Mapped[str | None]
    youtube_duration_seconds: Mapped[int | None]

    crowdin_file_id: Mapped[int | None]
    crowdin_project_id: Mapped[int | None]
    crowdin_translation_progress: Mapped[float | None]
    crowdin_approval_progress: Mapped[float | None]
    crowdin_url: Mapped[str | None]


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


def new_product_to_orm(product: NewLangOpsProduct) -> LangOpsProductORM:
    return LangOpsProductORM(
        date_created=datetime.now(),
        date_deleted=None,
        media_groups=product.media_groups,
        product_status=product.product_status,
        
        trello_id=product.trello_data.id,
        trello_url=str(product.trello_data.url) if product.trello_data.url else None,
        trello_title=product.trello_data.title,
        trello_localized_title=product.trello_data.localized_title if product.trello_data.localized_title else None,
        trello_product_code=product.trello_data.product_code,
        trello_target_language=product.trello_data.target_language,
        trello_due_date=product.trello_data.due_date,
        trello_date_last_activity=product.trello_data.date_last_activity,
        trello_date_published=product.trello_data.date_published,
        trello_date_archived=product.trello_data.date_archived,
        trello_article_url=str(product.trello_data.article_url) if product.trello_data.article_url else None,
        trello_editor_url=str(product.trello_data.editor_url) if product.trello_data.editor_url else None,
        trello_word_count=product.trello_data.word_count,

        crowdin_file_id=product.crowdin_data.crowdin_file_id if product.crowdin_data.crowdin_file_id else None,
        crowdin_project_id=product.crowdin_data.crowdin_project_id if product.crowdin_data.crowdin_project_id else None,
        crowdin_url=str(product.crowdin_data.crowdin_url) if product.crowdin_data.crowdin_url else None,
        crowdin_translation_progress=product.crowdin_data.translation_progress if product.crowdin_data.translation_progress else None,
        crowdin_approval_progress=product.crowdin_data.approval_progress if product.crowdin_data.approval_progress else None,

        youtube_id=product.youtube_data.id if product.youtube_data.id else None,
        youtube_url=str(product.youtube_data.url) if product.youtube_data.url else None,
        youtube_localized_title=product.youtube_data.localized_title if product.youtube_data.localized_title else None,
        youtube_duration_seconds=product.youtube_data.duration_seconds if product.youtube_data.duration_seconds else None

    )
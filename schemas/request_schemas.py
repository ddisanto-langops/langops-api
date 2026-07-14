from datetime import datetime
from pydantic import BaseModel, HttpUrl

from enums import ProductCodes, MediaGroups, Languages
from schemas.data_schemas import RawTrelloCard, RawCrowdinData


class AddProductRequest(BaseModel):
    trello_data: RawTrelloCard
    crowdin_data: RawCrowdinData


class EditProductRequest(BaseModel):
    
    media_groups: list[MediaGroups] | None = None
    
    # trello
    trello_title: str | None = None
    trello_url: HttpUrl | None = None
    trello_product_code: ProductCodes | None = None
    trello_target_language: Languages | None = None
    trello_due_date: datetime | None = None
    trello_date_published: datetime | None = None
    trello_editor_url: HttpUrl | None = None
    trello_article_url: HttpUrl | None = None
    trello_word_count: int | None = None
    # youtube
    youtube_id: str | None = None
    youtube_localized_title: str | None = None
    youtube_url: HttpUrl | None = None
    youtube_duration_seconds: int | None = None
    # crowdin
    crowdin_id: str | None = None
    crowdin_translation_progress: float | None = None
    crowdin_approval_progress: float | None = None
    crowdin_url: HttpUrl | None = None
    # soft delete
    date_deleted: datetime | None = None
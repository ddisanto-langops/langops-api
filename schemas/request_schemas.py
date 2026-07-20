from datetime import datetime
from pydantic import BaseModel

from enums import ProductCodes, MediaGroups, Languages
from schemas.data_schemas import RawTrelloCard, RawCrowdinData


class AddProductRequest(BaseModel):
    trello_data: RawTrelloCard
    crowdin_data: RawCrowdinData


class UserEditProductRequest(BaseModel):
    date_created: datetime | None = None
    date_deleted: datetime | None = None
    media_groups: list[MediaGroups] | None = None
    product_status: str | None = None

    trello_id: str | None = None
    trello_url: str | None = None
    trello_title: str | None = None
    trello_localized_title: str | None = None
    trello_product_code: ProductCodes | None = None
    trello_target_language: Languages | None = None
    trello_due_date: datetime | None = None
    trello_date_published: datetime | None = None
    trello_date_last_activity: datetime | None = None
    trello_date_archived: datetime | None = None
    trello_editor_url: str | None = None
    trello_article_url: str | None = None
    trello_word_count: int | None = None

    youtube_id: str | None = None
    youtube_localized_title: str | None = None
    youtube_url: str | None = None
    youtube_duration_seconds: int | None = None

    crowdin_file_id: int | None = None
    crowdin_project_id: int | None = None
    crowdin_translation_progress: float | None = None
    crowdin_approval_progress: float | None = None
    crowdin_url: str | None = None
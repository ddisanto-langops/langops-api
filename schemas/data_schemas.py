from uuid import UUID
from datetime import datetime
from enums import MediaGroups, ProductStatus
from pydantic import BaseModel, HttpUrl

from schemas.sub_schemas import (
    TrelloAction,
    TrelloAttachment,
    TrelloLabel,
    CustomFieldItem,
    TrelloData,
    YouTubeData,
    CrowdinData,
    StringMapPayload
)

# --------------------------------------
# Raw data classes, used in requests
# --------------------------------------

class RawTrelloCard(BaseModel):
    id: str
    name: str
    labels: list[TrelloLabel] | None 
    due: datetime | None
    date_last_activity: datetime
    url: HttpUrl
    is_template: bool
    date_closed: datetime
    actions: list[TrelloAction]
    attachments: list[TrelloAttachment] | None
    custom_field_items: list[CustomFieldItem] | None
    id_labels: list[str]

    class Config:
        populate_by_name = True 


class RawCrowdinData(BaseModel):
    translation_progress: int
    approval_progress: int






# --------------------------------------
# Product data classes, used in responses
# --------------------------------------

class ProductCodeCount(BaseModel):
    product_code: str
    count: int


class StringMapItem(BaseModel):
    context_identifier: str
    map: StringMapPayload


class LangOpsProduct(BaseModel):
    id: UUID
    date_created: datetime
    date_deleted: datetime | None
    media_groups: list[MediaGroups]
    product_status: ProductStatus
    trello_data: TrelloData | None
    youtube_data: YouTubeData | None
    crowdin_data: CrowdinData | None


class NewLangOpsProduct(BaseModel):
    date_created: datetime
    date_deleted: datetime | None = None
    media_groups: list[MediaGroups]
    product_status: ProductStatus
    trello_data: TrelloData | None
    youtube_data: YouTubeData | None
    crowdin_data: CrowdinData | None
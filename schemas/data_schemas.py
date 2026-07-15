from uuid import UUID
from datetime import datetime
from enums import MediaGroups, ProductStatus
from pydantic import BaseModel, HttpUrl, ConfigDict
from pydantic.alias_generators import to_camel

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
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    id: str
    name: str
    labels: list[TrelloLabel] | None = None
    due: datetime | None = None
    date_last_activity: datetime
    url: HttpUrl
    is_template: bool | None = None
    date_closed: datetime | None = None
    actions: list[TrelloAction] | None = None
    attachments: list[TrelloAttachment] | None = None
    custom_field_items: list[CustomFieldItem] | None = None
    id_labels: list[str] | None = None


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
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    date_created: datetime
    date_deleted: datetime | None = None
    media_groups: list[MediaGroups]
    product_status: ProductStatus
    trello_data: TrelloData | None
    youtube_data: YouTubeData | None
    crowdin_data: CrowdinData | None
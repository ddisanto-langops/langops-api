from uuid import UUID
from typing import Dict, Any
from datetime import datetime
from enums import MediaGroups, ProductStatus
from pydantic import HttpUrl, ConfigDict

from schemas.base import CamelModel
from schemas.sub_schemas import (
    TrelloAction,
    TrelloAttachment,
    TrelloLabel,
    CustomFieldItem,
    TrelloData,
    EditingTrelloData,
    YouTubeData,
    EditingYouTubeData,
    CrowdinData,
    EditingCrowdinData,
    StringMapPayload
)

# --------------------------------------
# Raw data classes, used in requests
# --------------------------------------

class RawTrelloCard(CamelModel):
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


class RawCrowdinData(CamelModel):
    translation_progress: int
    approval_progress: int






# --------------------------------------
# Product data classes, used in responses
# --------------------------------------

class ProductCodeCount(CamelModel):
    product_code: str
    count: int


class StringMapItem(CamelModel):
    context_identifier: str
    map: StringMapPayload


class LangOpsProduct(CamelModel):
    id: UUID
    date_created: datetime
    date_deleted: datetime | None
    media_groups: list[MediaGroups]
    product_status: ProductStatus
    trello_data: TrelloData | None
    youtube_data: YouTubeData | None
    crowdin_data: CrowdinData | None


class NewLangOpsProduct(CamelModel):
    date_created: datetime
    date_deleted: datetime | None = None
    media_groups: list[MediaGroups]
    product_status: ProductStatus
    trello_data: TrelloData | None
    youtube_data: YouTubeData | None
    crowdin_data: CrowdinData | None


class EditingLangOpsProduct(CamelModel):
    id: str | None = None
    date_created: datetime | None = None
    date_deleted: datetime | None = None
    media_groups: list[MediaGroups] | None = None
    product_status: ProductStatus | None = None

    trello_data: EditingTrelloData
    youtube_data: EditingYouTubeData | None = None 
    crowdin_data:  EditingCrowdinData | None = None


class NewWebhookFailure(CamelModel):
    status_code: str | None = None
    data: Dict[str, Any]


class WebhookFailure(CamelModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    date_created: datetime
    status_code: str | None = None
    data: Dict[str, Any]
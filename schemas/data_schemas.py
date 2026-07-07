from uuid import UUID
from datetime import datetime
from enums import ProductCodes, MediaGroups, Languages
from pydantic import BaseModel, ConfigDict, HttpUrl

from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl



class RawCrowdinData(BaseModel):
    pass




class TrelloLabel(BaseModel):
    id: str
    name: str

class CheckItem(BaseModel):
    id: str
    name: str
    state: str

class ActionData(BaseModel):
    check_item: CheckItem | None

class TrelloAction(BaseModel):
    data: ActionData
    type: str
    date: datetime  

class TrelloAttachment(BaseModel):
    name: str
    url: HttpUrl   

class CustomFieldValue(BaseModel):
    checked: str | None
    text: str | None

class CustomFieldItem(BaseModel):
    id_custom_field: str
    value: CustomFieldValue


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



class YouTubeLocalized(BaseModel):
    title: str

class YouTubeSnippet(BaseModel):
    localized: YouTubeLocalized

class YouTubeContentDetails(BaseModel):
    duration: str

class YouTubeItem(BaseModel):
    snippet: YouTubeSnippet
    content_details: YouTubeContentDetails

class RawYouTubeData(BaseModel):
    items: list[YouTubeItem]



class TrelloData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: HttpUrl
    title: str
    localized_title: str
    product_code: ProductCodes 
    target_language: Languages
    due_date: datetime | None
    date_published: datetime | None
    date_last_activity: datetime
    date_archived: datetime | None
    editor_url: HttpUrl | None
    article_url: HttpUrl | None
    word_count: int | None


class YouTubeData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    localized_title: str
    url: HttpUrl
    duration_seconds: int


class CrowdinData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crowdin_file_id: str | None
    translation_progress: float | None
    approval_progress: float | None
    crowdin_url: HttpUrl | None


class ProductCodeCount(BaseModel):
    product_code: str
    count: int


class StringMapPayload(BaseModel):
    string_ids: list[int]
    strings: list[str]
    label_id: int | None


class StringMapItem(BaseModel):
    context_identifier: str
    map: StringMapPayload


class LangOpsProduct(BaseModel):
    id: UUID
    date_created: datetime
    date_deleted: datetime | None
    media_groups: list[MediaGroups]
    product_status: str
    trello_data: TrelloData | None
    youtube_data: YouTubeData | None
    crowdin_data: CrowdinData | None


class NewLangOpsProduct(BaseModel):
    date_created: datetime
    date_deleted: datetime | None = None
    media_groups: list[MediaGroups]
    product_status: str
    trello_data: TrelloData | None
    youtube_data: YouTubeData | None
    crowdin_data: CrowdinData | None
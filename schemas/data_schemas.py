from datetime import datetime
from enums import ProductCodes, MediaGroups, Languages
from pydantic import BaseModel, ConfigDict, HttpUrl


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
    media_groups: list[MediaGroups]
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

    crowdin_id: str | None
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
        
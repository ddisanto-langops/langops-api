from datetime import datetime
from enums import ProductCodes, Languages
from pydantic import ConfigDict, HttpUrl

from schemas.base import CamelModel


# ---------------------
# TRELLO
# ---------------------

class TrelloLabel(CamelModel):
    id: str
    name: str

class CheckItem(CamelModel):
    id: str
    name: str
    state: str

class CustomFieldValue(CamelModel):
    checked: str | None = None
    text: str | None = None

class CustomFieldItem(CamelModel):
    id_custom_field: str | None = None
    value: CustomFieldValue | None = None

class ActionData(CamelModel):
    custom_field_item: CustomFieldItem | None = None
    check_item: CheckItem | None = None


class TrelloAction(CamelModel):
    data: ActionData | None = None
    type: str
    date: datetime  

class TrelloAttachment(CamelModel):
    name: str
    url: HttpUrl   




class TrelloData(CamelModel):
    model_config = ConfigDict(
        from_attributes=True,  
    )

    id: str
    url: HttpUrl
    title: str
    localized_title: str | None = None
    product_code: ProductCodes 
    target_language: Languages
    due_date: datetime | None = None
    date_published: datetime | None = None
    date_last_activity: datetime
    date_archived: datetime | None = None
    editor_url: HttpUrl | None = None
    article_url: HttpUrl | None = None
    word_count: int | None = None


class EditingTrelloData(CamelModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: str | None = None
    url: HttpUrl | None = None
    title: str | None = None
    localized_title: str | None = None
    product_code: ProductCodes | None = None
    target_language: Languages | None = None
    due_date: datetime | None = None
    date_published: datetime | None = None
    date_last_activity: datetime
    date_archived: datetime | None = None
    editor_url: HttpUrl | None = None
    article_url: HttpUrl | None = None
    word_count: int | None = None

# ---------------------
# IDML OPS
# ---------------------

class StringMapPayload(CamelModel):
    string_ids: list[int]
    strings: list[str]
    label_id: int | None = None



# ---------------------
# YouTube
# ---------------------

class YouTubeData(CamelModel):
    id: str | None = None
    localized_title: str | None = None
    url: HttpUrl | None = None
    duration_seconds: int | None = None


class EditingYouTubeData(YouTubeData):
    model_config = ConfigDict(from_attributes=True)
    pass



# ---------------------
# Crowdin
# ---------------------

class CrowdinData(CamelModel):
    model_config = ConfigDict(from_attributes=True)

    crowdin_file_id: int | None = None
    crowdin_project_id: int | None = None
    translation_progress: float | None = None
    approval_progress: float | None = None
    crowdin_url: HttpUrl | None = None


class EditingCrowdinData(CrowdinData):
    model_config = ConfigDict(from_attributes=True)
    pass
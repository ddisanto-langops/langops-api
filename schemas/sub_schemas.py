from datetime import datetime
from enums import ProductCodes, Languages
from pydantic import BaseModel, ConfigDict, HttpUrl


# ---------------------
# TRELLO
# ---------------------

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


# ---------------------
# IDML OPS
# ---------------------

class StringMapPayload(BaseModel):
    string_ids: list[int]
    strings: list[str]
    label_id: int | None



# ---------------------
# YouTube
# ---------------------

class YouTubeData(BaseModel):
    id: str | None
    localized_title: str | None
    url: HttpUrl | None
    duration_seconds: int | None




# ---------------------
# Crowdin
# ---------------------

class CrowdinData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crowdin_file_id: str | None
    crowdin_project_id: str | None
    translation_progress: float | None
    approval_progress: float | None
    crowdin_url: HttpUrl | None
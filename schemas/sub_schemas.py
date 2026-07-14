from datetime import datetime
from enums import ProductCodes, Languages
from pydantic import BaseModel, ConfigDict, HttpUrl
from pydantic.alias_generators import to_camel


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
    model_config = ConfigDict(alias_generator=to_camel)
    check_item: CheckItem | None = None

class TrelloAction(BaseModel):
    data: ActionData
    type: str
    date: datetime  

class TrelloAttachment(BaseModel):
    name: str
    url: HttpUrl   

class CustomFieldValue(BaseModel):
    checked: str | None = None
    text: str | None = None

class CustomFieldItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)
    id_custom_field: str
    value: CustomFieldValue | None = None


class TrelloData(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, 
        alias_generator=to_camel, 
        populate_by_name=True
    )

    id: str
    url: HttpUrl
    title: str
    localized_title: str
    product_code: ProductCodes 
    target_language: Languages
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

class StringMapPayload(BaseModel):
    string_ids: list[int]
    strings: list[str]
    label_id: int | None = None



# ---------------------
# YouTube
# ---------------------

class YouTubeData(BaseModel):
    id: str | None
    localized_title: str | None = None
    url: HttpUrl | None
    duration_seconds: int | None = None




# ---------------------
# Crowdin
# ---------------------

class CrowdinData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crowdin_file_id: int | None = None
    crowdin_project_id: int | None = None
    translation_progress: float | None = None
    approval_progress: float | None = None
    crowdin_url: HttpUrl | None = None
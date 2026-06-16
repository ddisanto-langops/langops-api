from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from enums import ProductCodes, MediaGroups, Languages
from pydantic import BaseModel, ConfigDict, Field


# --------------
# Sub-schemas (data/helpers)
# --------------

class TrelloData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    title: str
    product_code: ProductCodes 
    target_language: Languages
    due_date: Optional[datetime]
    date_published: Optional[datetime]
    date_last_activity: datetime
    media_groups: list[MediaGroups]
    editor_url: Optional[str]
    article_url: Optional[str]
    word_count: Optional[int]


class YouTubeData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    localized_title: str
    url: str
    duration_seconds: int


class CrowdinData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crowdin_id: Optional[str]
    translation_progress: Optional[float]
    approval_progress: Optional[float]
    crowdin_url: Optional[str]


class ProductCodeCount(BaseModel):
    product_code: str
    count: int



# --------------
# Request Schemas
# --------------

class EditProductRequest(BaseModel):
    # trello
    trello_title: Optional[str] = None
    trello_url: Optional[str] = None
    trello_product_code: Optional[ProductCodes] = None
    trello_target_language: Optional[Languages] = None
    trello_due_date: Optional[datetime] = None
    trello_date_published: Optional[datetime] = None
    trello_media_groups: Optional[list[MediaGroups]] = None
    trello_editor_url: Optional[str] = None
    trello_article_url: Optional[str] = None
    trello_word_count: Optional[int] = None
    # youtube
    youtube_id: Optional[str] = None
    youtube_localized_title: Optional[str] = None
    youtube_url: Optional[str] = None
    youtube_duration_seconds: Optional[int] = None
    # crowdin
    crowdin_id: Optional[str] = None
    crowdin_translation_progress: Optional[float] = None
    crowdin_approval_progress: Optional[float] = None
    crowdin_url: Optional[str] = None
    # soft delete
    date_deleted: Optional[datetime] = None



# --------------
# Response Schemas
# --------------

class CheckHealthResponse(BaseModel):
    status: str = "OK"
    database_version: str


class GetProductResponse(BaseModel):
    id: UUID
    date_created: datetime
    date_deleted: Optional[datetime]
    trello_data: Optional[TrelloData]
    youtube_data: Optional[YouTubeData]
    crowdin_data: Optional[CrowdinData]


class AddProductResponse(BaseModel):
    total_products_added: int
    data: list[GetProductResponse]


class PaginatedProductResponse(BaseModel):
    total: int
    offset: int
    limit: int
    data: list[GetProductResponse]


class EditProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # trello
    trello_title: Optional[str] = None
    trello_url: Optional[str] = None
    trello_product_code: Optional[ProductCodes] = None
    trello_target_language: Optional[Languages] = None
    trello_due_date: Optional[datetime] = None
    trello_date_published: Optional[datetime] = None
    trello_media_groups: Optional[list[MediaGroups]] = None
    trello_editor_url: Optional[str] = None
    trello_article_url: Optional[str] = None
    trello_word_count: Optional[int] = None
    # youtube
    youtube_id: Optional[str] = None
    youtube_localized_title: Optional[str] = None
    youtube_url: Optional[str] = None
    youtube_duration_seconds: Optional[int] = None
    # crowdin
    crowdin_id: Optional[str] = None
    crowdin_translation_progress: Optional[float] = None
    crowdin_approval_progress: Optional[float] = None
    crowdin_url: Optional[str] = None
    # soft delete
    date_deleted: Optional[datetime] = None



class DeleteResponse(BaseModel):
    id: UUID
    deleted_at: datetime


class RestoreResponse(BaseModel):
    id: UUID
    restored_at: datetime


class WordcountResponse(BaseModel):
    total_words: int


class ProductCodeCountResponse(BaseModel):
    total_products: int
    data: list[ProductCodeCount]
    

class ProductError(BaseModel):
    status_code: int
    detail: str
    path: str
    timestamp: datetime
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from enums import ProductCodes, MediaGroups, Languages
from pydantic import BaseModel, ConfigDict, Field


# --------------
# Data Schemas
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




# --------------
# Response Schemas
# --------------

class CheckHealthResponse(BaseModel):
    status: str = "OK"
    database_version: str


class ProductResponse(BaseModel):
    id: UUID
    date_created: datetime
    date_deleted: Optional[datetime]
    trello_data: Optional[TrelloData]
    youtube_data: Optional[YouTubeData]
    crowdin_data: Optional[CrowdinData]


class PaginatedProductResponse(BaseModel):
    total: int
    offset: int
    limit: int
    results: list[ProductResponse]

class ProductError(BaseModel):
    status_code: int
    detail: str
    path: str
    timestamp: datetime

class DeleteResponse(BaseModel):
    id: UUID
    deleted_at: datetime


class RestoreResponse(BaseModel):
    id: UUID
    restored_at: datetime


class WordcountResponse(BaseModel):
    total_words: int


class CountedProduct(BaseModel):
    product_code: str
    count: int

class ProductCountResponse(BaseModel):
    total_products: int
    products: list[CountedProduct]
    

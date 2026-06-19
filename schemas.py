from datetime import datetime
from pydantic import BaseModel, HttpUrl
from uuid import UUID
from enums import ProductCodes, MediaGroups, Languages
from pydantic import BaseModel, ConfigDict


# --------------
# Sub-schemas (data/helpers)
# --------------

class TrelloData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: HttpUrl
    title: str
    product_code: ProductCodes 
    target_language: Languages
    due_date: datetime | None
    date_published: datetime | None
    date_last_activity: datetime
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



# --------------
# Request Schemas
# --------------

class EditProductRequest(BaseModel):
    # trello
    trello_title: str | None = None
    trello_url: HttpUrl | None = None
    trello_product_code: ProductCodes | None = None
    trello_target_language: Languages | None = None
    trello_due_date: datetime | None = None
    trello_date_published: datetime | None = None
    trello_media_groups: list[MediaGroups] | None = None
    trello_editor_url: HttpUrl | None = None
    trello_article_url: HttpUrl | None = None
    trello_word_count: int | None = None
    # youtube
    youtube_id: str | None = None
    youtube_localized_title: str | None = None
    youtube_url: HttpUrl | None = None
    youtube_duration_seconds: int | None = None
    # crowdin
    crowdin_id: str | None = None
    crowdin_translation_progress: float | None = None
    crowdin_approval_progress: float | None = None
    crowdin_url: HttpUrl | None = None
    # soft delete
    date_deleted: datetime | None = None


# --------------
# Response Schemas
# --------------

class CheckHealthResponse(BaseModel):
    status: str = "OK"
    database_version: str


class GetProductResponse(BaseModel):
    id: UUID
    date_created: datetime
    date_deleted: datetime | None
    trello_data: TrelloData | None
    youtube_data: YouTubeData | None
    crowdin_data: CrowdinData | None


class AddProductResponse(BaseModel):
    total_products_added: int
    data: list[GetProductResponse]


class PaginatedProductResponse(BaseModel):
    total: int
    offset: int
    limit: int
    data: list[GetProductResponse]


class EditProductResponse(EditProductRequest):
    model_config = ConfigDict(from_attributes=True)


class DeleteProductResponse(BaseModel):
    id: UUID
    deleted_at: datetime


class RestoreProductResponse(BaseModel):
    id: UUID
    restored_at: datetime


class WordcountResponse(BaseModel):
    total_words: int


class ProductCodeCountResponse(BaseModel):
    total_products: int
    data: list[ProductCodeCount]
    

class StoreIdmlResponse(BaseModel):
    id: int


class ReconstructIDMLResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    status: str
    created_at: datetime
    updated_at: datetime
    crowdin_file_ids: list[int]
    crowdin_project_id: str | None
    target_language: str | None
    xliff_zip_data: bytes
    idml_data: bytes


class GetIDMLResponse(BaseModel):
    id: int
    file_name: str
    status: str

class ProductError(BaseModel):
    status_code: int
    detail: str
    path: str
    timestamp: datetime
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from schemas.data_schemas import TrelloData, YouTubeData, CrowdinData, ProductCodeCount
from schemas.request_schemas import EditProductRequest


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


class GetIDMLResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    file_name: str
    project: str = Field(validation_alias="crowdin_project_name")
    target_language: str
    status: str
    crowdin_file_ids: list[int] = Field(default_factory=list)
    date_created: datetime = Field(validation_alias="created_at")


class StoreIdmlResponse(BaseModel):
    id: UUID


class ReconstructIDMLResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_name: str
    status: str
    created_at: datetime
    updated_at: datetime
    crowdin_file_ids: list[int]
    crowdin_project_id: str | None
    target_language: str | None
    rebuilt_available: bool = False
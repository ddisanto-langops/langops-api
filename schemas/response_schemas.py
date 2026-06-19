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
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    project: str = Field(validation_alias="crowdin_project_name")
    target_language: str
    status: str
    date_created: datetime = Field(validation_alias="created_at")

class ProductError(BaseModel):
    status_code: int
    detail: str
    path: str
    timestamp: datetime
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from schemas.data_schemas import TrelloData, YouTubeData, CrowdinData, ProductCodeCount, StringMapItem
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


class GetStringMapResponse(BaseModel):
    data: list[StringMapItem]


class TrelloWebhookResponse(BaseModel):
    action_type: str
    action_date: datetime
    card_id: str
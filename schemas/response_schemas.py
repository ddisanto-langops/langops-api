from datetime import datetime
from pydantic import BaseModel, ConfigDict

from schemas.data_schemas import LangOpsProduct, NewLangOpsProduct, ProductCodeCount, StringMapItem
from schemas.request_schemas import UserEditProductRequest


class CheckHealthResponse(BaseModel):
    status: str = "OK"
    database_version: str
    


class AddProductResponse(BaseModel):
    total_products_added: int
    data: list[NewLangOpsProduct]


class PaginatedProductResponse(BaseModel):
    total: int
    offset: int
    limit: int
    data: list[LangOpsProduct]


class EditProductResponse(UserEditProductRequest):
    model_config = ConfigDict(from_attributes=True)


class DeleteProductResponse(BaseModel):
    id: str
    deleted_at: datetime


class RestoreProductResponse(BaseModel):
    id: str
    restored_at: datetime


class WordcountResponse(BaseModel):
    total_words: int


class ProductCodeCountResponse(BaseModel):
    total_products: int
    data: list[ProductCodeCount]


class GetStringMapResponse(BaseModel):
    data: list[StringMapItem]
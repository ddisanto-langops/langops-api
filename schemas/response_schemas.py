from datetime import datetime
from pydantic import ConfigDict

from schemas.base import CamelModel
from schemas.data_schemas import LangOpsProduct, NewLangOpsProduct, ProductCodeCount, StringMapItem
from schemas.request_schemas import UserEditProductRequest


class CheckHealthResponse(CamelModel):
    status: str = "OK"
    database_version: str
    


class AddProductResponse(CamelModel):
    total_products_added: int
    data: list[NewLangOpsProduct]


class PaginatedProductResponse(CamelModel):
    total: int
    offset: int
    limit: int
    data: list[LangOpsProduct]


class EditProductResponse(UserEditProductRequest):
    model_config = ConfigDict(from_attributes=True)


class DeleteProductResponse(CamelModel):
    id: str
    deleted_at: datetime


class RestoreProductResponse(CamelModel):
    id: str
    restored_at: datetime


class WordcountResponse(CamelModel):
    total_words: int


class ProductCodeCountResponse(CamelModel):
    total_products: int
    data: list[ProductCodeCount]


class GetStringMapResponse(CamelModel):
    data: list[StringMapItem]
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import asc, func, insert, update, delete, text, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Annotated
from uuid import UUID

from schemas import (
    CheckHealthResponse, 
    GetProductResponse,
    AddProductResponse,
    PaginatedProductResponse, 
    EditProductResponse,
    EditProductRequest,
    ProductError, 
    DeleteResponse, 
    RestoreResponse, 
    WordcountResponse, 
    ProductCodeCountResponse
) 

from models import LangOpsProductORM, orm_to_langops_product
from enums import MediaGroups, ProductCodes
from db import get_db

app = FastAPI(title="PCG LangOps API")



@app.get(
        "/api/health",
        response_model=CheckHealthResponse,
        responses={
            500: { "model": ProductError, "response_description": "Internal server error" }
        }
    )
async def check_health(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT version();"))
        db_version = result.scalar()
        return {
            "status": "OK",
            "database_version": db_version
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to get Postgres version: check that database is online. Message: {e}")
    


@app.get(
        "/api/products", 
        response_model=PaginatedProductResponse, 
        responses={
            400: { "model": ProductError, "response_description": "Bad request" },
            404: { "model": ProductError, "response_description": "Record not found" },
            500: { "model": ProductError, "response_description": "Internal server error" }
            }
        )
async def get_all_products(
    language: Annotated[str | None, Query(description="The target language of the product in ISO-639-1 format")] = None,
    date_from: Annotated[datetime | None, Query(description="Date the product was published")] = None,
    date_to: Annotated[datetime | None, Query(description="Date the product was published")] = None,
    product_code: Annotated[ProductCodes | None, Query(description="The prefixed code indicating type of product, e.g. 'PT'")] = None, 
    media_groups: Annotated[list[MediaGroups] | None, Query(description="The general category of the product, e.g. website")] = None, 
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
    offset: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    published_only: Annotated[bool, Query(description="Whether to return only products where date published is not null")] = False,
    deleted_only: Annotated[bool, Query(description="Whether to return deleted products only (where date deleted is not null)")] = False,
    db: AsyncSession = Depends(get_db)
    ):
    try:
        if limit > 500 or limit < 1:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 500.")
        
        

        statement = select(LangOpsProductORM).order_by(asc(LangOpsProductORM.date_created)).limit(limit).offset(offset)
        count_statement = select(func.count()).select_from(LangOpsProductORM)
        

        if language:
            statement = statement.where(LangOpsProductORM.trello_target_language == language)
            count_statement = count_statement.where(LangOpsProductORM.trello_target_language == language)

        if product_code:
            statement = statement.where(LangOpsProductORM.trello_product_code == product_code)
            count_statement = count_statement.where(LangOpsProductORM.trello_product_code == product_code)
        
        if date_from and date_to:
            statement = statement.where(LangOpsProductORM.trello_date_published.between(date_from, date_to))
            count_statement = count_statement.where(LangOpsProductORM.trello_date_published.between(date_from, date_to))
        
        if media_groups:
            values = [g.value for g in media_groups]
            statement = statement.where(
                or_(*[LangOpsProductORM.trello_media_groups.any(v) for v in values])
            )
            count_statement = count_statement.where(
                or_(*[LangOpsProductORM.trello_media_groups.any(v) for v in values])
            )
        
        if published_only:
            statement = statement.where(LangOpsProductORM.trello_date_published.is_not(None))
            count_statement = count_statement.where(LangOpsProductORM.trello_date_published.is_not(None))

        if deleted_only:
            statement =  statement.where(LangOpsProductORM.date_deleted.is_not(None))
            count_statement = count_statement.where(LangOpsProductORM.date_deleted.is_not(None))
        
        result = await db.execute(statement)
        rows = result.scalars().all()

        if not rows:
            raise HTTPException(status_code=404, detail="No records found")
        

        total = await db.scalar(count_statement)

        return PaginatedProductResponse(
            total=total,
            offset=offset,
            limit=limit,
            data=[orm_to_langops_product(r) for r in rows]
        )
        
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {e}")


@app.get(
        "/api/products/{id}",
        description="Get a product by its unique ID",
        response_model=GetProductResponse,
        responses={
            400: { "model": ProductError, "response_description": "Bad request" },
            404: { "model": ProductError, "response_description": "Record not found" },
            500: { "model": ProductError, "response_description": "Internal server error" }
        }
)
async def get_product_by_id(
    id: Annotated[UUID, Path(description="The unique ID of the product (not a Trello or Crowdin ID)")],
    db: AsyncSession = Depends(get_db)
):
    try:
        statement = select(LangOpsProductORM).where(LangOpsProductORM.id == id)
        await db.execute(statement)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product by ID: {e}")



@app.get(
        "/api/products/wordcount",
        description="Gets the sum of all word counts in LangOps products for published products only. Ignores unpublished and deletions.",
        response_model=WordcountResponse,
        responses={
            400: { "model": ProductError, "response_description": "Bad request" },
            404: { "model": ProductError, "response_description": "Record not found" },
            500: { "model": ProductError, "response_description": "Internal server error" }
        }
)
async def get_word_count(
    language: Annotated[str | None, Query(description="The target language of the product in ISO-639-1 format")] = None,
    date_from: Annotated[datetime | None, Query(description="Date the product was published")] = None,
    date_to: Annotated[datetime | None, Query(description="Date the product was published")] = None,
    product_code: Annotated[ProductCodes | None, Query(description="The prefixed code indicating type of product, e.g. 'PT'")] = None, 
    media_groups: Annotated[list[MediaGroups] | None, Query(description="The general category of the product, e.g. website")] = None, 
    db: AsyncSession = Depends(get_db)
):
    try:
        statement = (
            select(
                func.coalesce(func.sum(LangOpsProductORM.trello_word_count), 0)
            )
            .where(LangOpsProductORM.trello_word_count.is_not(None))
            .where(LangOpsProductORM.trello_date_published.is_not(None))
            .where(LangOpsProductORM.date_deleted.is_(None))
        )

        if language:
            statement = statement.where(LangOpsProductORM.trello_target_language == language)
        
        if date_from and date_to:
            statement = statement.where(LangOpsProductORM.trello_date_published.between(date_from, date_to))
        
        if product_code:
            statement = statement.where(LangOpsProductORM.trello_product_code == product_code)
        
        if media_groups:
            values = [g.value for g in media_groups]
            statement = statement.where(
                or_(*[LangOpsProductORM.trello_media_groups.any(v) for v in values])
            )
        

        total_words = await db.scalar(statement)

        return WordcountResponse(
            total_words=total_words
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to get word count: {e}")



@app.get(
        "/api/products/productcount",
        description="Gets the count of each product code in LangOps products for published products only. Ignores unpublished and deletions.",
        response_model=ProductCodeCountResponse,
        responses={
            400: { "model": ProductError, "response_description": "Bad request" },
            404: { "model": ProductError, "response_description": "Record not found" },
            500: { "model": ProductError, "response_description": "Internal server error" }
        }
)
async def get_product_count(
    language: Annotated[str | None, Query(description="The target language of the product in ISO-639-1 format")] = None,
    date_from: Annotated[datetime | None, Query(description="Date the product was published")] = None,
    date_to: Annotated[datetime | None, Query(description="Date the product was published")] = None,
    product_code: Annotated[ProductCodes | None, Query(description="The prefixed code indicating type of product, e.g. 'PT'")] = None, 
    media_groups: Annotated[list[MediaGroups] | None, Query(description="The general category of the product, e.g. website")] = None, 
    db: AsyncSession = Depends(get_db)
):
    try:
        filters = [
            LangOpsProductORM.trello_product_code.is_not(None),
            LangOpsProductORM.trello_date_published.is_not(None),
            LangOpsProductORM.date_deleted.is_(None),
        ]

        if language:
            filters.append(LangOpsProductORM.trello_target_language == language)
        
        if date_from and date_to:
            filters.append(LangOpsProductORM.trello_date_published.between(date_from, date_to))
        
        if product_code:
            filters.append(LangOpsProductORM.trello_product_code == product_code)
        
        if media_groups:
            values = [g.value for g in media_groups]
            filters.append(or_(*[LangOpsProductORM.trello_media_groups.any(v) for v in values]))
        
        total_statement = select(func.count(LangOpsProductORM.trello_product_code)).where(*filters)

        grouped_statement = (
            select(
                LangOpsProductORM.trello_product_code.label("product_code"),
                func.count().label("count")
            )
            .where(*filters)
            .group_by(LangOpsProductORM.trello_product_code)
            .order_by(LangOpsProductORM.trello_product_code.asc())
        )
        
        total_products = await db.scalar(total_statement)
        grouped_result = await db.execute(grouped_statement)
        rows = grouped_result.all()

        return ProductCodeCountResponse(
            total_products=total_products or 0,
            count=[
                {"product_code": row.product_code, "count": row.count} for row in rows
            ]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to get product count: {e}")


@app.post(
    "/api/products/add",
    description="Add a product or multiple products to the database",
    response_model=AddProductResponse,
    responses={
        400: { "model": ProductError, "response_description": "Bad request" },
        404: { "model": ProductError, "response_description": "Record not found" },
        500: { "model": ProductError, "response_description": "Internal server error" }
    }
)
async def add_products(
    products: Annotated[list[GetProductResponse], Body(description="The fields for a LangOps product")],
    db: AsyncSession = Depends(get_db)      
):
    try:
        await db.execute(insert(LangOpsProductORM), products)
        await db.commit()
        
        return AddProductResponse(
            total_products_added= len(products),
            data=products
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to add products: {e}")


@app.patch(
    "/api/products/restore/{id}",
    description="Restore a soft-deleted product",
    response_model=RestoreResponse,
    responses={
        400: { "model": ProductError, "response_description": "Bad request" },
        404: { "model": ProductError, "response_description": "Record not found" },
        500: { "model": ProductError, "response_description": "Internal server error" }
    }
)
async def restore_product(
    id: Annotated[UUID, Path(description="The unique ID of the product (not a Trello or Crowdin ID)")],
    db: AsyncSession = Depends(get_db)
):
    try:
        statement = update(LangOpsProductORM).where(LangOpsProductORM.id == id).values(date_deleted=None).returning(LangOpsProductORM.id)
        result = await db.execute(statement)
        await db.commit()

        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Product not found")


        return RestoreResponse(
            id=id,
            restored_at=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore record: {e}")


@app.patch(
        "/api/products/edit/{id}",
        description="Edit an existing product",
        response_model=EditProductResponse,
        responses={
            400: { "model": ProductError, "response_description": "Bad request" },
            404: { "model": ProductError, "response_description": "Record not found" },
            500: { "model": ProductError, "response_description": "Internal server error" }
        }
)
async def edit_product(
    id: Annotated[UUID, Path(description="The unique ID of the product (not a Trello or Crowdin ID)")],
    updated_product: Annotated[EditProductRequest, Body()],
    db: AsyncSession = Depends(get_db)
):
    try:
        fields = updated_product.model_dump(exclude_unset=True)
        if not fields:
            raise HTTPException(status_code=400, detail="Must provide fields to update")
        
        statement = update(LangOpsProductORM).where(LangOpsProductORM.id == id).values(**fields).returning(LangOpsProductORM)

        result = await db.execute(statement)
        await db.commit()

        row = result.scalar_one_or_none() 
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")

        return EditProductResponse.model_validate(row)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to edit record: {e}")


@app.delete(
    "/api/products/delete/{id}",
    description="Soft delete of a product",
    response_model=DeleteResponse, 
    responses={
        400: { "model": ProductError, "response_description": "Bad request" },
        404: { "model": ProductError, "response_description": "Record not found" },
        500: { "model": ProductError, "response_description": "Internal server error" }
    }
)
async def delete_product(
    id: Annotated[UUID, Path(description="The unique ID of the product (not a Trello or Crowdin ID)")],
    db: AsyncSession = Depends(get_db)
):
    try:
        timestamp = datetime.now(timezone.utc)
        statement = (
            update(LangOpsProductORM)
                .where(LangOpsProductORM.id == id)
                .values(date_deleted=timestamp)
        )

        result = await db.execute(statement)
        await db.commit()

        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Unable to soft-delete product: not found")

        return DeleteResponse(
            id=id,
            deleted_at=timestamp
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete record: {e}")


@app.delete(
        "/api/products/permanentdelete/{id}",
        description="**Hard delete** of a product",
        response_model=DeleteResponse,
        responses={
            400: { "model": ProductError, "response_description": "Bad request" },
            404: { "model": ProductError, "response_description": "Record not found" },
            500: { "model": ProductError, "response_description": "Internal server error" }
        }
)
async def permanently_delete_product(
    id: Annotated[UUID, Path(description="The unique ID of the product (not a Trello or Crowdin ID)")],
    db: AsyncSession = Depends(get_db)
):
    try:
        statement = delete(LangOpsProductORM).where(LangOpsProductORM.id == id).returning(LangOpsProductORM.id)
        result = await db.execute(statement)
        await db.commit()

        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Unable to permanently delete product: not found")

        return DeleteResponse(
            id=id,
            deleted_at=datetime.now(timezone.utc)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to permanently delete record: {e}")



# TODO:
# 1. Add edit product endpoint - this should include the ability to update "stale" active products
# 2. Add IDML endpoints



# -------------------
# EXCEPTION HANDLERS
# -------------------


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status_code": 422, "detail": exception.errors()[0]["msg"]}
    )

@app.exception_handler(StarletteHTTPException)
def general_exception_handler(request: Request, exception: StarletteHTTPException):
    return JSONResponse(
        status_code= exception.status_code,
        content = {
            "status_code": exception.status_code,
            "detail": exception.detail or "An unknown error has occurred",
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
import os
import json
import httpx
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body, Form, File, UploadFile
from fastapi.requests import Request
from fastapi.responses import Response, JSONResponse
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
    ProductCodeCountResponse,
    StoreIdmlResponse,
    GetIDMLResponse,
    ReconstructIDMLResponse
) 

from functions import get_idml_record

from models import LangOpsProductORM, orm_to_langops_product, IdmlStorageORM
from enums import MediaGroups, ProductCodes
from constants import *
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
    language: Annotated[str | None, Query(
        title="Target Language", 
        alias="targetLanguage", 
        description="The target language of the products in ISO-639-1 format"
    )] = None,
    date_from: Annotated[datetime | None, Query(
        title="Date From", 
        alias="dateFrom", 
        description="Return products published on or after this date"
    )] = None,
    date_to: Annotated[datetime | None, Query(
        title="Date To", 
        alias="dateTo", 
        description="Return products published on or before this date"
    )] = None,
    product_code: Annotated[ProductCodes | None, Query(
        title="Product Code",
        alias="productCode",
        description="The prefixed code indicating type of product, e.g. 'PT'",
        max_length=PRODUCT_CODE_MAX_LEN
    )] = None, 
    media_groups: Annotated[list[MediaGroups] | None, Query(
        title="Media Groups",
        alias="mediaGroups",
        description="The general category of the product, e.g. website"
    )] = None, 
    limit: Annotated[int, Query(
        title="Limit",
        alias="limit",
        ge=1,
        le=500
    )] = 500,
    offset: Annotated[int, Query(
         title="Offset",
         alias="offset",
        description="Number of records to skip",
        ge=0
    )] = 0,
    published_only: Annotated[bool, Query(
        title="Published Only",
        alias="publishedOnly",
        description="""Whether to return only products where `date_published` **is not null.**
        <span style="color:red">If set to true, `unpublished_only` must be set to false.</span>"""
    )] = False,
    unpublished_only: Annotated[bool, Query(
        title="Unpublished Only",
        alias="unpublishedOnly",
        description="""Whether to return only products where `date_published` **is null.**
        <span style="color:red">If set to true, `published_only` must be set to false.</span>"""
    )] = False,
    exclude_deleted: Annotated[bool, Query(
        title="Exclude Deleted",
        alias="excludeDeleted",
        description="""Whether to exclude deleted products 
        (where date deleted is not null). If set to false, 
        deleted products will be returned along with active ones.
        """
    )] = True,
    db: AsyncSession = Depends(get_db)
    ):
    try:
        if limit > 500 or limit < 1:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 500.")
        
        
        # Default behavior: select all products within limit and offset, order ascending.
        # NOTE: Excludes deleted products by default, unless exclude_deleted is set to True
        statement = (
            select(LangOpsProductORM)
            .order_by(asc(LangOpsProductORM.date_created))
            .limit(limit)
            .offset(offset)
        )
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
        
        if unpublished_only:
            statement = statement.where(LangOpsProductORM.trello_date_published.is_(None))
            count_statement = count_statement.where(LangOpsProductORM.trello_date_published.is_(None))

        if exclude_deleted:
            statement = statement.where(LangOpsProductORM.date_deleted.is_(None))
            count_statement = count_statement.where(LangOpsProductORM.date_deleted.is_(None))
        
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
        description="""Gets the sum of all word counts in LangOps products, 
        for published products only. Ignores unpublished and deletions.""",
        response_model=WordcountResponse,
        responses={
            400: { "model": ProductError, "response_description": "Bad request" },
            404: { "model": ProductError, "response_description": "Record not found" },
            500: { "model": ProductError, "response_description": "Internal server error" }
        }
)
async def get_word_count(
    language: Annotated[str | None, Query(
        title="Target Language", 
        alias="targetLanguage", 
        description="The target language of the products in ISO-639-1 format"
    )] = None,
    date_from: Annotated[datetime | None, Query(
        title="Date From", 
        alias="dateFrom", 
        description="Return products published on or after this date"
    )] = None,
    date_to: Annotated[datetime | None, Query(
        title="Date To", 
        alias="dateTo", 
        description="Return products published on or before this date"
    )] = None,
    product_code: Annotated[ProductCodes | None, Query(
        title="Product Code",
        alias="productCode",
        description="The prefixed code indicating type of product, e.g. 'PT'",
        max_length=PRODUCT_CODE_MAX_LEN
    )] = None, 
    media_groups: Annotated[list[MediaGroups] | None, Query(
        title="Media Groups",
        alias="mediaGroups",
        description="The general category of the product, e.g. website"
    )] = None, 
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
    language: Annotated[str | None, Query(
        title="Target Language", 
        alias="targetLanguage", 
        description="The target language of the products in ISO-639-1 format"
    )] = None,
    date_from: Annotated[datetime | None, Query(
        title="Date From", 
        alias="dateFrom", 
        description="Return products published on or after this date"
    )] = None,
    date_to: Annotated[datetime | None, Query(
        title="Date To", 
        alias="dateTo", 
        description="Return products published on or before this date"
    )] = None,
    product_code: Annotated[ProductCodes | None, Query(
        title="Product Code",
        alias="productCode",
        description="The prefixed code indicating type of product, e.g. 'PT'",
        max_length=PRODUCT_CODE_MAX_LEN
    )] = None, 
    media_groups: Annotated[list[MediaGroups] | None, Query(
        title="Media Groups",
        alias="mediaGroups",
        description="The general category of the product, e.g. website"
    )] = None, 
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


@app.get(
    "/api/idml/list",
    description="Lists the IDMLs present in the LangOps IDML storage table",
    response_model=list[GetIDMLResponse],
    responses={
        400: { "model": ProductError, "response_description": "Bad request" },
        404: { "model": ProductError, "response_description": "Record not found" },
        500: { "model": ProductError, "response_description": "Internal server error" }
    }
)
async def list_idmls(
    db: AsyncSession = Depends(get_db)
):
    try:
        statement = select(IdmlStorageORM)
        result = await db.execute(statement)
        rows = result.scalars().all()
        
        return [
            {
                "id": row.id,
                "file_name": row.file_name,
                "status": row.status,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            } 
            for row in rows
        ]
    
    except HTTPException:
        raise HTTPException(status_code=404, detail="No records found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to get IDML records: {e}")


@app.post(
    "/api/products/add",
    description="Add a product or multiple products to the database",
    response_model=AddProductResponse,
    status_code=201,
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


@app.post(
    "/api/idml/parse",
    description="""Sends an .idml file to be parsed into individual XLIFFs by the LangOps IDML handler service.
    This returns multiple XLIFF files which correspond to the stories inside the .idml file.""",
    response_class=Response,
    status_code=201,
    responses={
        400: { "model": ProductError, "response_description": "Bad request" },
        500: { "model": ProductError, "response_description": "Internal server error" },
        502: { "model": ProductError, "response_description": "Upstream error" }
    }
)
async def parse_idml(
    file: UploadFile = File(title="IDML File", alias="idmlFile", description="The inDesign file to be parsed"),
    source_language: str = Form(default="en", title="Source Language", alias="sourceLanguage")
    
):
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="No file provided")

    cf_client_id = os.environ["CF_ACCESS_CLIENT_ID"]
    cf_client_secret = os.environ["CF_ACCESS_CLIENT_SECRET"]

    async with httpx.AsyncClient(timeout=60.0) as client:
        upstream = await client.post(
            "https://idml.pcglangops.com/parse",
            headers={
                "CF-Access-Client-Id": cf_client_id,
                "CF-Access-Client-Secret": cf_client_secret
            },
            files={"idml": (file.filename, file_bytes, "application/octet-stream")},
            data={"source_lang": source_language}
        )
    
    if not upstream.is_success:
        raise HTTPException(status_code=502, detail=f"Upstream Status {upstream.status_code}: {upstream.text}")

    return Response(
        status_code=201,
        content=upstream.content,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=parsed.zip"}
    )


@app.post(
    "/api/idml/store",
    description="""Stores the parsed XLIFF files and original IDML
    in the LangOps IDML database for future reconstruction""",
    status_code=201,
    response_model=StoreIdmlResponse,
    responses={
        400: { "model": ProductError, "response_description": "Bad request" },
        500: { "model": ProductError, "response_description": "Internal server error" },
        502: { "model": ProductError, "response_description": "Upstream error" }
    }
)
async def store_idml(
    idml_file: UploadFile = File(alias="idml"),
    xliff_zip: UploadFile = File(alias="xliffZip"),
    file_name: str = Form(alias="fileName"),
    crowdin_project_id: str | None = Form(default=None, alias="projectId"),
    crowdin_project_name: str | None = Form(default=None, alias="projectName"),
    target_language: str | None = Form(default=None, alias="targetLanguage"),
    crowdin_file_ids: str = Form(default="[]", alias="crowdinFileIds"),
    db: AsyncSession = Depends(get_db)
):
    try:
        parsed_ids = json.loads(crowdin_file_ids)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="crowdinFileIds must be a JSON array")

    idml_bytes = await idml_file.read()
    zip_bytes = await xliff_zip.read()

    if not idml_bytes or not zip_bytes:
        raise HTTPException(status_code=400, detail="Both idml and xliffZip files are required")

    try:
        record = IdmlStorageORM(
            file_name=file_name,
            idml_data=idml_bytes,
            xliff_zip_data=zip_bytes,
            crowdin_project_id=crowdin_project_id,
            crowdin_project_name=crowdin_project_name,
            target_language=target_language,
            crowdin_file_ids=parsed_ids,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return {"id": record.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store IDML record: {e}")

# TODO: Finish building reconstruct
@app.post(
    "/api/idml/reconstruct/{id}",
    description="""Reconstructs an IDML file from translated XLIFF files,
    via the LangOps IDML database.""",
    status_code=201,
    response_model=ReconstructIDMLResponse,
    responses={
        400: { "model": ProductError, "response_description": "Bad request" },
        500: { "model": ProductError, "response_description": "Internal server error" },
        502: { "model": ProductError, "response_description": "Upstream error" }
    }
)
async def reconstruct_idml(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        record = await get_idml_record(id, db)

        if record is None:
            raise HTTPException(status_code=404, detail="Record not found")
        


        return ReconstructIDMLResponse(
            id=record.id,
            file_name=record.file_name,
            status=record.status,
            crowdin_file_ids=record.crowdin_file_ids
        )

    except HTTPException as e:
        raise HTTPException(status_code=500, detail=f"IDML reconstruct failed: {e}")


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
    updated_product: Annotated[EditProductRequest, Body(alias="updatedProduct")],
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